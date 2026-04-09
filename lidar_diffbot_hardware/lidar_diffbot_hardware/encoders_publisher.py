#!/usr/bin/env python

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

DEFAULT_WHEEL_SEPARATION = 0.18

class EncodersPublisher(Node):
    
    def __init__(self):
        super().__init__("encoders_publisher")

        self.declare_parameter("wheel_separation", DEFAULT_WHEEL_SEPARATION)
        self.wheel_separation = float(self.get_parameter("wheel_separation").value)

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            depth=10
        )

        # Subscriber
        self.joint_state_subscriber_ = self.create_subscription(
            JointState, "/encoders/data_raw", self.joint_state_callback, qos_profile)
    
        # Publishers: JointState and Twist
        self.joint_state_publisher_ = self.create_publisher(
            JointState, "/joint_states", 10)
        
        self.twist_publisher_ = self.create_publisher(
            Twist, "/twist_states", 10)

        self.get_logger().info("encoders_publisher has been started")

    def joint_state_callback(self, msg: JointState):
        # Republish the JointState msg by joint_state_publisher_
        self.joint_state_publisher_.publish(msg)

        # Publish a Twist msg by twist_publisher_
        left_vel = msg.velocity[0]
        right_vel = msg.velocity[1]
        linear_x = (right_vel + left_vel) / 2
        angular_z = (right_vel - left_vel) / self.wheel_separation

        twist_msg = Twist()
        twist_msg.linear.x = linear_x
        twist_msg.angular.z = angular_z
        self.twist_publisher_.publish(twist_msg)

def main(args=None):
    rclpy.init(args=args)
    node = EncodersPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()