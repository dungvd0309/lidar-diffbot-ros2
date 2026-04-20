#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
	pkg_share = get_package_share_directory('lidar_diffbot_navigation')
	default_params_file = os.path.join(pkg_share, 'config', 'navigation.yaml')
	default_map_file = os.path.join(pkg_share, 'map', 'my_map.yaml')

	use_sim_time = LaunchConfiguration('use_sim_time')
	params_file = LaunchConfiguration('params_file')
	map_file = LaunchConfiguration('map')
	autostart = LaunchConfiguration('autostart')

	declare_use_sim_time = DeclareLaunchArgument(
		'use_sim_time',
		default_value='false',
		description='Use simulation (Gazebo) clock if true',
	)

	declare_params_file = DeclareLaunchArgument(
		'params_file',
		default_value=default_params_file,
		description='Full path to Nav2 params file',
	)

	declare_map_file = DeclareLaunchArgument(
		'map',
		default_value=default_map_file,
		description='Full path to map yaml file',
	)

	declare_autostart = DeclareLaunchArgument(
		'autostart',
		default_value='true',
		description='Automatically startup the nav2 stack',
	)

	nav2_bringup = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(
				get_package_share_directory('nav2_bringup'),
				'launch',
				'bringup_launch.py',
			)
		),
		launch_arguments={
				'slam': 'False',
			'map': map_file,
			'use_sim_time': use_sim_time,
			'params_file': params_file,
			'autostart': autostart,
				'use_composition': 'False',
		}.items(),
	)

	return LaunchDescription([
		declare_use_sim_time,
		declare_params_file,
		declare_map_file,
		declare_autostart,
		nav2_bringup,
	])
