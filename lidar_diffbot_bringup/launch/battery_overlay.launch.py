from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='lidar_diffbot_bringup',
            executable='battery_overlay',
            name='battery_overlay',
            output='screen',
        ),
        Node(
            package='rviz_2d_overlay_plugins',
            executable='string_to_overlay_text',
            name='battery_overlay_bridge',
            output='screen',
            parameters=[
                {"string_topic": "/battery_text_raw"},
                {"fg_color": "g"}
            ]
        ),
    ])
