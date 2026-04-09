#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    config_file = os.path.join(
        get_package_share_directory('lidar_diffbot_hardware'),
        'config',
        'robot_params.yaml'
    )

    micro_ros_publisher = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        arguments=['serial', '--dev', '/dev/serial0']
    )

    encoders_publisher = Node(
        package='lidar_diffbot_hardware',
        executable='encoders_publisher',
        name='encoders_publisher',
        output='screen',
        parameters=[config_file]
    )

    ydlidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ydlidar_ros2_driver'),
                'launch',
                'ydlidar_launch.py'
            )
        )
    )

    return LaunchDescription([
        micro_ros_publisher,
        encoders_publisher, 
        ydlidar_launch

    ])