"""
Full exploration launch — starts robot hardware + auto_mapper

This is a convenience launch file that brings up:
  1. lidar_diffbot robot (description + hardware)
  2. auto_mapper (SLAM + Nav2 + frontier exploration)

Usage:
  ros2 launch auto_mapper explore.launch.py map_path:=~/maps/my_map

If you already have the robot running (robot.launch.py), use auto_mapper.launch.py instead.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    map_path = LaunchConfiguration('map_path')
    use_sim_time = LaunchConfiguration('use_sim_time')

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

    # Launch robot hardware (description + drivers)
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('lidar_diffbot_bringup'),
                'launch',
                'robot.launch.py'
            ])
        ),
    )

    # Launch auto_mapper (SLAM + Nav2 + exploration)
    auto_mapper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('auto_mapper'),
                'launch',
                'auto_mapper.launch.py'
            ])
        ),
        launch_arguments={
            'map_path': map_path,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    return LaunchDescription(
        declared_arguments + [
            robot_launch,
            auto_mapper_launch,
        ]
    )
