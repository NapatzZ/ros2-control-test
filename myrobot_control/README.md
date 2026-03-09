# ros2-control-test

## Setup
```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-joint-state-broadcaster ros-humble-joint-trajectory-controller

cd ~/test_ws && colcon build --packages-select my_robot_control && source install/setup.bash
```

## Run → Get

| Command | Result |
|---------|--------|
| `ros2 launch my_robot_control control.launch.py` | Normal version (Mock Hardware + RViz) |
| `ros2 launch my_robot_control condition_control.launch.py use_mock_hardware:=true` | Conditional version (Mock Hardware + RViz) |
| `ros2 launch my_robot_control condition_control.launch.py use_mock_hardware:=false` | Conditional version (Real Dynamixel — requires motors) |

## Test → Move

> Keep launch running in terminal 1, open **terminal 2**:
```bash
ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  '{joint_names: ["arm_base_link_link_1", "arm_link_1_arm_link_2"],
    points: [{positions: [1.57, -1.57], time_from_start: {sec: 2, nanosec: 0}}]}' -1
```

**→ Joints rotate to 90° / −90° over 2 seconds in RViz.**
