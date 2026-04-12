#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_share = get_package_share_directory('lidar_diffbot_description')
    default_model_path = os.path.join(pkg_share, 'urdf', 'colored_lidar_diffbot.urdf')

    # Launch arguments
    model_arg = DeclareLaunchArgument(
        'model',
        default_value=default_model_path,
        description='Absolute path to robot URDF file',
    )

    robot_description_content = ParameterValue(
        Command(['cat ', LaunchConfiguration('model')]),
        value_type=str,
    )

    # Launch executables
    robot_state_publisher = Node(
        package='robot_state_publisher',    
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}],
    )


    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        output='screen',
        condition=UnlessCondition(LaunchConfiguration('gui')),
    )

    return LaunchDescription([
        model_arg,
        robot_state_publisher,
        joint_state_publisher,
    ])