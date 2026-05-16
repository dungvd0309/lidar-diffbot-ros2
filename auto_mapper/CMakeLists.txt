cmake_minimum_required(VERSION 3.8)
project(auto_mapper)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_CXX_STANDARD 17)

find_package(ament_cmake REQUIRED)

set(deps
  rclcpp
  rclcpp_action
  geometry_msgs
  nav_msgs
  nav2_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
  nav2_costmap_2d
  nav2_map_server
  nav2_util
  slam_toolbox
  visualization_msgs
  std_msgs
  map_msgs
)

foreach(d ${deps})
  find_package(${d} REQUIRED)
endforeach()

add_executable(auto_mapper src/auto_mapper.cpp)
ament_target_dependencies(auto_mapper ${deps})

install(TARGETS
  auto_mapper
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY config launch rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
