import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String


class BatteryOverlay(Node):
    def __init__(self):
        super().__init__('battery_overlay')
        self.sub = self.create_subscription(
            BatteryState, '/battery_state', self.cb, 10
        )
        self.pub = self.create_publisher(String, '/battery_text_raw', 10)

    def cb(self, msg: BatteryState):
        pct = 0.0 if math.isnan(msg.percentage) else msg.percentage
        volt = "N/A" if math.isnan(msg.voltage) else f"{msg.voltage:.1f}V"

        out = String()
        out.data = f"BAT: {pct:.0f}% \n VOL: {volt}"
        self.pub.publish(out)


def main():
    rclpy.init()
    node = BatteryOverlay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()