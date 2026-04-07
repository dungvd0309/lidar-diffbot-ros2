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
    default_rviz_config_path = os.path.join(pkg_share, 'rviz', 'default.rviz')

    # Launch arguments
    model_arg = DeclareLaunchArgument(
        'model',
        default_value=default_model_path,
        description='Absolute path to robot URDF file',
    )
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Start joint_state_publisher_gui',
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Start RViz2',
    )
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config_path,
        description='Absolute path to RViz config file',
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

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen',
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription(
        [
            model_arg,
            gui_arg,
            rviz_arg,
            rviz_config_arg,
            robot_state_publisher,
            joint_state_publisher,
            joint_state_publisher_gui,
            rviz2,
        ]
    )
