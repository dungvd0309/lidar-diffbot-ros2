# lidar-diffbot-ros2

ROS 2 packages for a differential-drive robot with LIDAR, SLAM, navigation, and autonomous exploration. 

<img width="500" height="500" alt="robot_pic" src="https://github.com/user-attachments/assets/11d7f795-ffd3-4c5b-8679-49c54d89d182" />

[Demo video on YouTube](https://youtu.be/oauRnWwvWOY?t=132)

## Firmware
Firmware and hardware details are documented here:
https://github.com/dungvd0309/lidar-diffbot-firmware

## 1. Key features

- Robot description (URDF) + bringup launch files
- EKF fusion for encoder and IMU data
- SLAM via slam_toolbox
- Navigation via Nav2
- Auto exploration via auto_mapper

## 2. Requirement
### Hardware
- ESP32 DevKit
- Raspberry Pi 4 
- YDLIDAR X3
- JGA25 DC motors with encoders + 65mm blue wheels
- BNO055 IMU
- 12V battery pack
- 3D printed robot frame

### Software

- ROS 2 Humble
- colcon + rosdep
- SLAM toolbox
- Nav2
- rviz_2d_overlay_plugins (for battery overlay)
- [YDLIDAR SDK](https://github.com/YDLIDAR/YDLidar-SDK)
- [YDLIDAR ROS 2 driver](https://github.com/YDLIDAR/ydlidar_ros2_driver/tree/humble) built and sourced

## 3. Installation
```bash
# Create workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Clone repo
git clone https://github.com/dungvd0309/lidar-diffbot-ros2

# Install dependencies
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y

# Build workspace
colcon build
source install/setup.bash
```

## 4. How to start

### a) Run robot bringup

This starts the robot description and hardware drivers (run on Raspberry Pi 4)

```bash
ros2 launch lidar_diffbot_bringup robot.launch.py
```

### b) Run SLAM or Navigation

Open RViz

```bash
ros2 launch lidar_diffbot_bringup rviz.launch.py
```

SLAM (create a new map):

```bash
ros2 launch lidar_diffbot_navigation slam.launch.py
```

Navigation (requires an existing map):

```bash
ros2 launch lidar_diffbot_navigation navigation.launch.py map:=/path/to/map.yaml
```

### c) Auto exploration 

Auto explore and save map:

```bash
ros2 launch auto_mapper auto_mapper.launch.py map_path:=~/maps/my_map
```

## Package overview

- auto_mapper: auto exploration 
- lidar_diffbot_bringup: bringup + RViz launch
- lidar_diffbot_description: URDF + model
- lidar_diffbot_hardware: hardware drivers + EKF
- lidar_diffbot_navigation: SLAM + Nav2 config

## Reference repositories

- https://github.com/kaiaai/auto_mapper
