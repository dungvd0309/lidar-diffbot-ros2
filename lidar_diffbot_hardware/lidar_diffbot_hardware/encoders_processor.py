#!/usr/bin/env python

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from nav_msgs.msg import Odometry
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

DEFAULT_WHEEL_SEPARATION = 0.18

class EncodersProcessor(Node):
    
    def __init__(self):
        super().__init__("encoders_processor")

        self.declare_parameter("wheel_separation", DEFAULT_WHEEL_SEPARATION)
        self.wheel_separation = float(self.get_parameter("wheel_separation").value)

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            depth=10
        )

        # Subscriber
        self.joint_state_subscriber_ = self.create_subscription(
            JointState, "/encoders/data_raw", self.joint_state_callback, qos_profile)
    
        # Publishers: JointState and Odometry
        self.joint_state_publisher_ = self.create_publisher(
            JointState, "/joint_states", 10)
        
        self.odom_publisher_ = self.create_publisher(
            Odometry, "/encoders/odom", 10)

        self.get_logger().info("encoders_processor has been started")

    def joint_state_callback(self, msg: JointState):
        # Republish the JointState msg by joint_state_publisher_
        self.joint_state_publisher_.publish(msg)

        # Publish wheel-based odometry twist on /encoders/odom
        left_vel = msg.velocity[0]
        right_vel = msg.velocity[1]
        linear_x = (right_vel + left_vel) / 2
        angular_z = (right_vel - left_vel) / self.wheel_separation

        odom_msg = Odometry()
        odom_msg.header.stamp = msg.header.stamp
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_link"
        odom_msg.twist.twist.linear.x = linear_x
        odom_msg.twist.twist.angular.z = angular_z
        self.odom_publisher_.publish(odom_msg)

def main(args=None):
    rclpy.init(args=args)
    node = EncodersProcessor()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()