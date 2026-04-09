cmake_minimum_required(VERSION 3.8)

project(lidar_diffbot_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    urdf
    meshes
    config
    launch
    world
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
