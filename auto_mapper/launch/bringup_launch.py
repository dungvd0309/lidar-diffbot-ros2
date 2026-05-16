"""
Nav2 navigation-only bringup for auto_mapper.

This launches ONLY the navigation stack (controller, planner, behavior, bt_navigator, etc.)
WITHOUT localization (AMCL/map_server) since SLAM Toolbox provides the map→odom transform.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    package_name = LaunchConfiguration('package_name')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    log_level = LaunchConfiguration('log_level')

    nav2_params_file_path = PathJoinSubstitution(
        [FindPackageShare(package_name), 'config', 'nav2_params.yaml'])

    declare_package_name_cmd = DeclareLaunchArgument(
        'package_name',
        default_value='auto_mapper',
        description='Package name for finding config files')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=nav2_params_file_path,
        description='Full path to the ROS2 parameters file')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically startup the nav2 stack')

    declare_log_level_cmd = DeclareLaunchArgument(
        'log_level', default_value='info',
        description='log level')

    # Rewrite params with use_sim_time
    param_substitutions = {'use_sim_time': use_sim_time}
    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True)

    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1')

    # Navigation nodes (no localization — SLAM provides map→odom)
    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'waypoint_follower',
        'velocity_smoother',
    ]

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level])

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'node_names': lifecycle_nodes,
        }])

    ld = LaunchDescription()

    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_package_name_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_log_level_cmd)

    ld.add_action(controller_server)
    ld.add_action(smoother_server)
    ld.add_action(planner_server)
    ld.add_action(behavior_server)
    ld.add_action(bt_navigator)
    ld.add_action(waypoint_follower)
    ld.add_action(velocity_smoother)
    ld.add_action(lifecycle_manager)

    return ld
