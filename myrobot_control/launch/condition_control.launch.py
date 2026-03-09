import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration  # <--- เพิ่ม LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'my_robot_control'
    pkg_share = get_package_share_directory(pkg_name)

    urdf_path = os.path.join(pkg_share, 'urdf', 'condition_robot.urdf.xacro')
    controller_params_file = os.path.join(pkg_share, 'config', 'controllers.yaml')

    # 1. ประกาศตัวรับ Argument จาก Terminal
    use_mock_arg = DeclareLaunchArgument(
        'use_mock_hardware',
        default_value='true',  # ค่าเริ่มต้น ถ้าไม่พิมพ์อะไรเลยให้เป็น true
        description='Set to true to use mock hardware, false for real Dynamixel'
    )

    # 2. ดึงค่าที่รับมาไปใช้งาน
    use_mock_config = LaunchConfiguration('use_mock_hardware')

    # 3. นำตัวแปรไปต่อท้ายคำสั่ง Xacro
    robot_description = {'robot_description': Command(['xacro ', urdf_path, ' use_mock_hardware:=', use_mock_config])}

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    node_controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controller_params_file],
        output='screen'
    )

    spawn_jsb = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    spawn_arm_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller', '--controller-manager', '/controller_manager'],
    )

    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen'
    )

    delay_jsb_after_cm = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_jsb,
            on_exit=[spawn_arm_controller],
        )
    )

    # ✨ จัดการปัญหาจราจรติดขัด: หน่วงเวลาเปิด RViz ไว้ 4.0 วินาที
    delay_rviz = TimerAction(
        period=4.0,
        actions=[node_rviz]
    )

    return LaunchDescription([
        use_mock_arg,            # <--- ต้องใส่ Argument เข้าไปในนี้ด้วย
        node_robot_state_publisher,
        node_controller_manager,
        spawn_jsb,
        delay_jsb_after_cm,
        delay_rviz,              
    ])
