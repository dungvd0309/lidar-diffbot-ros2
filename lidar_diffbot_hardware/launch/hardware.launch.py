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

    robot_params = os.path.join(
        get_package_share_directory('lidar_diffbot_hardware'),
        'config',
        'robot_params.yaml'
    )

    x3lidar_params = os.path.join(
        get_package_share_directory('lidar_diffbot_hardware'),
        'config',
        'X3.yaml'
    )

    micro_ros_publisher = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        arguments=['serial', '--dev', '/dev/serial0', '-b', '2000000'],
    )

    encoders_processor = Node(
        package='lidar_diffbot_hardware',
        executable='encoders_processor',
        namespace='encoders',
        name='processor',
        output='screen',
        parameters=[robot_params]
    )
    
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(get_package_share_directory('lidar_diffbot_hardware'), 'config', 'ekf.yaml')]
    )

    ydlidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ydlidar_ros2_driver'),
                'launch',
                'ydlidar_launch.py'
            )
        ),
        launch_arguments={
            'params_file': x3lidar_params
        }.items()
    )

    # tf2_node = Node(package='tf2_ros',
    #                 executable='static_transform_publisher',
    #                 name='static_tf_pub_laser',
    #                 arguments=['0', '0', '0','0', '0', '0', '0','base_footprint','odom'],
    #                 )

    return LaunchDescription([
        micro_ros_publisher,
        encoders_processor, 
        ekf_node,
        ydlidar_launch,
        # tf2_node
    ])