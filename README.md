# lidar-diffbot-ros2

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Firmware](https://img.shields.io/badge/Firmware-repo-blue)](https://github.com/dungvd0309/lidar-diffbot-firmware)
[![ROS2_packages](https://img.shields.io/badge/ROS2_packages-repo-blue)](https://github.com/dungvd0309/lidar-diffbot-ros2)

ROS 2 packages for a differential-drive robot with LIDAR, SLAM, navigation, and autonomous exploration. 

> **This is a two-repo project.** This repo contains the ROS 2 software stack. ESP32 firmware and hardware/wiring details are in [lidar-diffbot-firmware](https://github.com/dungvd0309/lidar-diffbot-firmware).

<div align="center">
  <img width="400" height="400" alt="robot_pic" src="https://github.com/user-attachments/assets/11d7f795-ffd3-4c5b-8679-49c54d89d182"/>

  *Demo video on [YouTube](https://youtu.be/oauRnWwvWOY?t=132)*
</div>

## Table of Contents
- [1. Key features](#1-key-features)
- [2. Requirements](#2-requirements)
- [3. Installation](#3-installation)
- [4. How to start](#4-how-to-start)
- [5. Package overview](#5-package-overview)

## 1. Key features

- Builds a 2D map of an unknown environment with SLAM.
- Autonomously explores and maps an area end-to-end, saving the finished map automatically when exploration completes.
- Navigates to any point on a saved map while avoiding obstacles in real time.
- Fuses wheel encoder and IMU data with EKF (Extend Kalman Filter) for more accurate localization.
- Visualizes robot state, map, and battery level live in RViz.

## 2. Requirements
### Hardware
- ESP32 DevKit
- Raspberry Pi 4 
- YDLIDAR X3
- 2x JGA25 DC motors with encoders + 2x 65mm blue wheels
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
- [YDLIDAR ROS 2 driver](https://github.com/YDLIDAR/ydlidar_ros2_driver/tree/humble) (built and sourced workspace)

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

###  Run robot bringup

- This starts the robot description and hardware drivers (run on Raspberry Pi 4)

```bash
ros2 launch lidar_diffbot_bringup robot.launch.py
```

### Run SLAM or Navigation

- Open RViz

```bash
ros2 launch lidar_diffbot_bringup rviz.launch.py
```

- SLAM (create a new map):

```bash
ros2 launch lidar_diffbot_navigation slam.launch.py
```

- Navigation (requires an existing map):

```bash
ros2 launch lidar_diffbot_navigation navigation.launch.py map:=/path/to/map.yaml
```

### Auto exploration 

- Auto explore and save map:

```bash
ros2 launch auto_mapper auto_mapper.launch.py map_path:=~/maps/my_map
```

## 5. Package overview

| Package | Description |
|---|---|
| `auto_mapper` | Autonomous frontier exploration and map saving |
| `lidar_diffbot_bringup` | Robot bringup + RViz launch files |
| `lidar_diffbot_description` | URDF + 3D model |
| `lidar_diffbot_hardware` | Hardware drivers + EKF sensor fusion |
| `lidar_diffbot_navigation` | SLAM + Nav2 configuration |

### Node graphs
<img width="394" height="300" alt="auto_mapper_graph" src="https://github.com/user-attachments/assets/4ab47fcc-44ec-4c91-85ea-b8f25b621b0d" />
<img width="595" height="300" alt="nav_graph" src="https://github.com/user-attachments/assets/35b7cc92-e198-406a-8c3e-fa068705a3bd" />

## Acknowledgements

- https://github.com/kaiaai/auto_mapper
