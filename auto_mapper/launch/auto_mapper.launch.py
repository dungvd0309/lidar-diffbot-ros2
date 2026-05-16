"""
auto_mapper launch file — adapted for lidar_diffbot_ros2

This launch file starts:
  1. SLAM Toolbox (async mapping mode)
  2. Nav2 navigation stack (for frontier navigation)
  3. auto_mapper node (frontier exploration)

Prerequisites:
  - Robot hardware must already be running (robot.launch.py from lidar_diffbot_bringup)
  - Topics available: /scan, /odom, /tf

Usage:
  ros2 launch auto_mapper auto_mapper.launch.py map_path:=~/maps/my_map
  ros2 launch auto_mapper auto_mapper.launch.py map_path:=~/maps/my_map use_sim_time:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare arguments
    declared_arguments = [
        DeclareLaunchArgument(
            'map_path',
            description='Full path (without extension) to save the map',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true',
        ),
    ]

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_path = LaunchConfiguration('map_path')
    package_name = 'auto_mapper'
    package_share = FindPackageShare(package_name)

    # --- SLAM Toolbox ---
    slam_params_file = PathJoinSubstitution(
        [package_share, 'config', 'mapper_params_online_async.yaml'])

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([package_share, 'launch', 'online_async_launch.py'])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam_params_file': slam_params_file,
            'map_file_name': map_path,
        }.items(),
    )

    # --- Nav2 Bringup (navigation only, SLAM provides map→odom tf) ---
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([package_share, 'launch', 'bringup_launch.py'])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'package_name': package_name,
        }.items(),
    )

    # --- auto_mapper frontier exploration node ---
    auto_mapper_node = Node(
        package=package_name,
        executable='auto_mapper',
        name='auto_mapper',
        output='screen',
        parameters=[{'map_path': map_path}],
    )

    # --- RViz (optional, for visualization) ---
    rviz_config_file = PathJoinSubstitution([package_share, 'rviz', 'config.rviz'])
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config_file],
    )

    # Group all actions
    exploration_group = GroupAction(
        actions=[
            slam_launch,
            nav2_bringup_launch,
            auto_mapper_node,
            rviz_node,
        ]
    )

    return LaunchDescription(declared_arguments + [exploration_group])
