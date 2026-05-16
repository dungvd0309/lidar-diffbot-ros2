//
// auto_mapper — Frontier-based autonomous exploration
// Adapted for lidar_diffbot_ros2
//
// Subscribes to /map (from SLAM Toolbox)
// Gets robot pose from TF (map → base_footprint)
// Finds frontier cells (boundary between known-free and unknown space)
// Sends navigation goals to Nav2 to explore frontiers
// Saves map periodically via slam_toolbox services
//

#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <array>
#include <algorithm>

#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/point.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "nav2_costmap_2d/costmap_2d.hpp"
#include "nav2_costmap_2d/cost_values.hpp"
#include "nav2_util/occ_grid_values.hpp"
#include "visualization_msgs/msg/marker_array.hpp"
#include "visualization_msgs/msg/marker.hpp"
#include "std_msgs/msg/color_rgba.hpp"
#include "nav2_map_server/map_mode.hpp"
#include "nav2_map_server/map_saver.hpp"
#include "slam_toolbox/srv/serialize_pose_graph.hpp"
#include "slam_toolbox/srv/save_map.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"


using std::placeholders::_1;
using geometry_msgs::msg::PoseStamped;
using geometry_msgs::msg::Point;
using nav_msgs::msg::OccupancyGrid;
using nav2_msgs::action::NavigateToPose;
using visualization_msgs::msg::MarkerArray;
using visualization_msgs::msg::Marker;
using std_msgs::msg::ColorRGBA;
using nav2_costmap_2d::Costmap2D;
using nav2_costmap_2d::LETHAL_OBSTACLE;
using nav2_costmap_2d::NO_INFORMATION;
using nav2_costmap_2d::FREE_SPACE;
using std::to_string;
using std::abs;
using namespace std::chrono_literals;
using namespace std;
using namespace rclcpp;
using namespace rclcpp_action;
using namespace nav2_map_server;
using namespace slam_toolbox;

using NavigateToPose = nav2_msgs::action::NavigateToPose;
using GoalHandleNavigateToPose = rclcpp_action::ClientGoalHandle<NavigateToPose>;

class AutoMapper : public Node {
public:
    AutoMapper()
            : Node("auto_mapper") {
        RCLCPP_INFO(get_logger(), "AutoMapper started...");

        // TF buffer for getting robot pose from map frame
        tf_buffer_ = std::make_shared<tf2_ros::Buffer>(get_clock());
        tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

        mapSubscription_ = create_subscription<OccupancyGrid>(
                "/map", 10, bind(&AutoMapper::updateFullMap, this, _1));

        markerArrayPublisher_ = create_publisher<MarkerArray>("/frontiers", 10);
        poseNavigator_ = rclcpp_action::create_client<NavigateToPose>(
                this,
                "/navigate_to_pose");

        RCLCPP_INFO(get_logger(), "Waiting for Nav2 action server...");
        poseNavigator_->wait_for_action_server();
        RCLCPP_INFO(get_logger(), "Nav2 action server connected");

        declare_parameter("map_path", rclcpp::PARAMETER_STRING);
        declare_parameter("base_frame", "base_footprint");
        declare_parameter("map_frame", "map");
        get_parameter("map_path", mapPath_);
        get_parameter("base_frame", baseFrame_);
        get_parameter("map_frame", mapFrame_);
    }

private:
    // Tuned for lidar_diffbot (small robot, 3cm map resolution, 3.5m LIDAR)
    const double MIN_FRONTIER_DENSITY = 0.15;       // meters of frontier edge
    const double MIN_DISTANCE_TO_FRONTIER = 0.5;    // don't go to very close frontiers
    const int MIN_FREE_THRESHOLD = 4;               // min free neighbors to be reachable
    Costmap2D costmap_;
    rclcpp_action::Client<NavigateToPose>::SharedPtr poseNavigator_;
    Publisher<MarkerArray>::SharedPtr markerArrayPublisher_;
    MarkerArray markersMsg_;
    Subscription<OccupancyGrid>::SharedPtr mapSubscription_;
    bool isExploring_ = false;
    int markerId_ = 0;
    string mapPath_;
    string baseFrame_;
    string mapFrame_;
    bool feedbackPrinted_ = false;

    // TF for pose lookup
    std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

    array<unsigned char, 256> costTranslationTable_ = initTranslationTable();

    static array<unsigned char, 256> initTranslationTable() {
        array<unsigned char, 256> cost_translation_table{};

        // linearly mapped from [0..100] to [0..255]
        for (size_t i = 0; i < 256; ++i) {
            cost_translation_table[i] =
                    static_cast<unsigned char>(1 + (251 * (i - 1)) / 97);
        }

        // special values:
        cost_translation_table[0] = FREE_SPACE;
        cost_translation_table[99] = 253;
        cost_translation_table[100] = LETHAL_OBSTACLE;
        cost_translation_table[static_cast<unsigned char>(-1)] = NO_INFORMATION;

        return cost_translation_table;
    }

    struct Frontier {
        Point centroid;
        vector<Point> points;
    };

    bool getRobotPose(double &x, double &y) {
        try {
            auto transform = tf_buffer_->lookupTransform(
                mapFrame_, baseFrame_, tf2::TimePointZero, 1s);
            x = transform.transform.translation.x;
            y = transform.transform.translation.y;
            return true;
        } catch (const tf2::TransformException &ex) {
            RCLCPP_WARN(get_logger(), "Could not get robot pose: %s", ex.what());
            return false;
        }
    }

    void updateFullMap(OccupancyGrid::UniquePtr occupancyGrid) {
        double robot_x, robot_y;
        if (!getRobotPose(robot_x, robot_y)) {
            return;
        }

        RCLCPP_INFO(get_logger(), "Map update received");
        const auto occupancyGridInfo = occupancyGrid->info;
        unsigned int size_in_cells_x = occupancyGridInfo.width;
        unsigned int size_in_cells_y = occupancyGridInfo.height;
        double resolution = occupancyGridInfo.resolution;
        double origin_x = occupancyGridInfo.origin.position.x;
        double origin_y = occupancyGridInfo.origin.position.y;

        costmap_.resizeMap(size_in_cells_x,
                           size_in_cells_y,
                           resolution,
                           origin_x,
                           origin_y);

        // lock as we are accessing raw underlying map
        auto *mutex = costmap_.getMutex();
        lock_guard<Costmap2D::mutex_t> lock(*mutex);

        // fill map with data
        unsigned char *costmap_data = costmap_.getCharMap();
        size_t costmap_size = costmap_.getSizeInCellsX() * costmap_.getSizeInCellsY();
        for (size_t i = 0; i < costmap_size && i < occupancyGrid->data.size(); ++i) {
            auto cell_cost = static_cast<unsigned char>(occupancyGrid->data[i]);
            costmap_data[i] = costTranslationTable_[cell_cost];
        }

        explore();
    }

    void drawMarkers(const vector<Frontier> &frontiers) {
        for (const auto &frontier: frontiers) {
            ColorRGBA green;
            green.r = 0;
            green.g = 1.0;
            green.b = 0;
            green.a = 1.0;

            vector<Marker> &markers = markersMsg_.markers;
            Marker m;

            m.header.frame_id = "map";
            m.header.stamp = now();
            m.frame_locked = true;

            m.action = Marker::ADD;
            m.ns = "frontiers";
            m.id = ++markerId_;
            m.type = Marker::SPHERE;
            m.pose.position = frontier.centroid;
            m.scale.x = 0.2;
            m.scale.y = 0.2;
            m.scale.z = 0.2;
            m.color = green;
            markers.push_back(m);
            markerArrayPublisher_->publish(markersMsg_);
        }
    }

    void clearMarkers() {
        for (auto &m: markersMsg_.markers) {
            m.action = Marker::DELETE;
        }
        markerArrayPublisher_->publish(markersMsg_);
    }

    void stop() {
        RCLCPP_INFO(get_logger(), "Exploration complete! Saving final map...");
        mapSubscription_.reset();
        poseNavigator_->async_cancel_all_goals();
        saveMap();
        clearMarkers();
    }

    void explore() {
        if (isExploring_) { return; }

        double robot_x, robot_y;
        if (!getRobotPose(robot_x, robot_y)) {
            return;
        }

        auto frontiers = findFrontiers(robot_x, robot_y);
        if (frontiers.empty()) {
            RCLCPP_WARN(get_logger(), "No more frontiers found — exploration complete!");
            stop();
            return;
        }
        const auto frontier = frontiers[0];
        drawMarkers(frontiers);
        auto goal = NavigateToPose::Goal();
        goal.pose.pose.position = frontier.centroid;
        goal.pose.pose.orientation.w = 1.;
        goal.pose.header.frame_id = "map";

        RCLCPP_INFO(get_logger(), "Navigating to frontier at (%.2f, %.2f) [%zu frontiers available]",
                    frontier.centroid.x, frontier.centroid.y, frontiers.size());

        auto send_goal_options = rclcpp_action::Client<NavigateToPose>::SendGoalOptions();
        send_goal_options.goal_response_callback = [this](
                const GoalHandleNavigateToPose::SharedPtr &goal_handle) {
            if (goal_handle) {
                RCLCPP_INFO(get_logger(), "Goal accepted, navigating...");
                isExploring_ = true;
            } else {
                RCLCPP_ERROR(get_logger(), "Goal rejected by Nav2");
            }
        };

        send_goal_options.feedback_callback = [this](
                const GoalHandleNavigateToPose::SharedPtr &,
                const std::shared_ptr<const NavigateToPose::Feedback> &feedback) {
            if (feedbackPrinted_)
              return;
            RCLCPP_INFO(get_logger(), "Distance remaining: %.2f", feedback->distance_remaining);
            feedbackPrinted_ = true;
        };

        send_goal_options.result_callback = [this](const GoalHandleNavigateToPose::WrappedResult &result) {
            isExploring_ = false;
            saveMap();
            clearMarkers();
            switch (result.code) {
                case rclcpp_action::ResultCode::SUCCEEDED:
                    RCLCPP_INFO(get_logger(), "Goal reached, looking for next frontier...");
                    break;
                case rclcpp_action::ResultCode::ABORTED:
                    RCLCPP_WARN(get_logger(), "Goal aborted, trying next frontier...");
                    break;
                case rclcpp_action::ResultCode::CANCELED:
                    RCLCPP_WARN(get_logger(), "Goal canceled");
                    break;
                default:
                    RCLCPP_ERROR(get_logger(), "Unknown result code");
                    break;
            }
            explore();
        };
        feedbackPrinted_ = false;
        poseNavigator_->async_send_goal(goal, send_goal_options);
    }

    void saveMap() {
        auto mapSerializer = create_client<slam_toolbox::srv::SerializePoseGraph>(
                "/slam_toolbox/serialize_map");
        auto serializePoseGraphRequest =
                std::make_shared<slam_toolbox::srv::SerializePoseGraph::Request>();
        serializePoseGraphRequest->filename = mapPath_;
        mapSerializer->async_send_request(serializePoseGraphRequest);

        auto map_saver = create_client<slam_toolbox::srv::SaveMap>(
                "/slam_toolbox/save_map");
        auto saveMapRequest = std::make_shared<slam_toolbox::srv::SaveMap::Request>();
        saveMapRequest->name.data = mapPath_;
        map_saver->async_send_request(saveMapRequest);
        RCLCPP_INFO(get_logger(), "Map save requested: %s", mapPath_.c_str());
    }

    vector<unsigned int> nhood8(unsigned int idx) {
        unsigned int mx, my;
        vector<unsigned int> out;
        costmap_.indexToCells(idx, mx, my);
        const int x = mx;
        const int y = my;
        const pair<int, int> directions[] = {
                {-1, -1}, {-1, 1}, {1, -1}, {1, 1},
                {1, 0}, {-1, 0}, {0, 1}, {0, -1}
        };
        for (const auto &d: directions) {
            int newX = x + d.first;
            int newY = y + d.second;
            if (newX > -1 && newX < int(costmap_.getSizeInCellsX()) &&
                newY > -1 && newY < int(costmap_.getSizeInCellsY())) {
                out.push_back(costmap_.getIndex(newX, newY));
            }
        }
        return out;
    }

    bool isAchievableFrontierCell(unsigned int idx,
                                  const vector<bool> &frontier_flag) {
        auto map = costmap_.getCharMap();
        // check that cell is unknown and not already marked as frontier
        if (map[idx] != NO_INFORMATION || frontier_flag[idx]) {
            return false;
        }

        // check there's enough free space for robot to move to frontier
        int freeCount = 0;
        for (unsigned int nbr: nhood8(idx)) {
            if (map[nbr] == FREE_SPACE) {
                if (++freeCount >= MIN_FREE_THRESHOLD) {
                    return true;
                }
            }
        }

        return false;
    }

    Frontier buildNewFrontier(unsigned int neighborCell, vector<bool> &frontier_flag) {
        Frontier output;
        output.centroid.x = 0;
        output.centroid.y = 0;

        queue<unsigned int> bfs;
        bfs.push(neighborCell);

        while (!bfs.empty()) {
            unsigned int idx = bfs.front();
            bfs.pop();

            for (unsigned int nbr: nhood8(idx)) {
                if (isAchievableFrontierCell(nbr, frontier_flag)) {
                    frontier_flag[nbr] = true;
                    unsigned int mx, my;
                    double wx, wy;
                    costmap_.indexToCells(nbr, mx, my);
                    costmap_.mapToWorld(mx, my, wx, wy);

                    Point point;
                    point.x = wx;
                    point.y = wy;
                    output.points.push_back(point);

                    output.centroid.x += wx;
                    output.centroid.y += wy;

                    bfs.push(nbr);
                }
            }
        }

        // average out frontier centroid
        output.centroid.x /= output.points.size();
        output.centroid.y /= output.points.size();
        return output;
    }

    vector<Frontier> findFrontiers(double robot_x, double robot_y) {
        vector<Frontier> frontier_list;
        unsigned int mx, my;
        if (!costmap_.worldToMap(robot_x, robot_y, mx, my)) {
            RCLCPP_ERROR(get_logger(), "Robot out of costmap bounds, cannot search for frontiers");
            return frontier_list;
        }

        // make sure map is consistent and locked for duration of search
        lock_guard<Costmap2D::mutex_t> lock(*(costmap_.getMutex()));

        auto map_ = costmap_.getCharMap();
        auto size_x_ = costmap_.getSizeInCellsX();
        auto size_y_ = costmap_.getSizeInCellsY();

        // initialize flag arrays
        vector<bool> frontier_flag(size_x_ * size_y_, false);
        vector<bool> visited_flag(size_x_ * size_y_, false);

        // BFS from robot position
        queue<unsigned int> bfs;
        unsigned int pos = costmap_.getIndex(mx, my);
        bfs.push(pos);
        visited_flag[pos] = true;

        while (!bfs.empty()) {
            unsigned int idx = bfs.front();
            bfs.pop();

            for (unsigned nbr: nhood8(idx)) {
                if (map_[nbr] == FREE_SPACE && !visited_flag[nbr]) {
                    visited_flag[nbr] = true;
                    bfs.push(nbr);
                } else if (isAchievableFrontierCell(nbr, frontier_flag)) {
                    frontier_flag[nbr] = true;
                    const Frontier frontier = buildNewFrontier(nbr, frontier_flag);

                    double distance = sqrt(pow(frontier.centroid.x - robot_x, 2.0) +
                                           pow(frontier.centroid.y - robot_y, 2.0));
                    if (distance < MIN_DISTANCE_TO_FRONTIER) { continue; }
                    if (frontier.points.size() * costmap_.getResolution() >=
                        MIN_FRONTIER_DENSITY) {
                        frontier_list.push_back(frontier);
                    }
                }
            }
        }

        // Sort frontiers by distance (closest first)
        std::sort(frontier_list.begin(), frontier_list.end(),
            [robot_x, robot_y](const Frontier &a, const Frontier &b) {
                double dist_a = sqrt(pow(a.centroid.x - robot_x, 2.0) +
                                     pow(a.centroid.y - robot_y, 2.0));
                double dist_b = sqrt(pow(b.centroid.x - robot_x, 2.0) +
                                     pow(b.centroid.y - robot_y, 2.0));
                return dist_a < dist_b;
            });

        return frontier_list;
    }
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<AutoMapper>());
    rclcpp::shutdown();
    return 0;
}
