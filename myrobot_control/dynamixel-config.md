# Dynamixel URDF Setup Guide (ros2_control) — The No-Fluff Version

A practical guide for ROS 2 robotics builders who want to control Dynamixel motors using the `dynamixel_hardware_interface` package through URDF / XACRO configuration.

---

## 1. The Hardware Block — Your Robot's Foundation

Think of this section as the main declaration that tells your system *how* the robot is connected: which USB port, at what speed, and where to find the motor model files. You **always** need this.

```xml
<hardware>
  <!-- Load the Dynamixel plugin -->
  <plugin>dynamixel_hardware_interface/DynamixelHardware</plugin>

  <!-- ⚠️ Required parameters — do NOT remove these -->
  <param name="number_of_joints">2</param>            <!-- Total number of joints -->
  <param name="number_of_transmissions">2</param>     <!-- Usually equals number of joints -->
  <param name="port_name">/dev/ttyUSB0</param>        <!-- USB port your motors are connected to -->
  <param name="baud_rate">1000000</param>             <!-- Communication speed in bps — must match the motor setting -->
  <param name="dynamixel_model_folder">/param/dxl_model/</param> <!-- Path to model XML files (relative to your package) -->

  <!-- Optional but recommended for stability and safety -->
  <param name="error_timeout_ms">500</param>          <!-- Cut off if motor read hangs longer than this (ms) -->
  <param name="disable_torque_at_init">false</param>  <!-- Set to true if you want the motors to be freely movable on startup -->
</hardware>
```

---

## 2. Operating Modes — What Do You Want the Motor to Do?

The very first thing to decide for each joint is its **operating mode** — basically, are you controlling position, speed, or force? Here's what each number means:

**`0` — Current Control Mode**
Control the motor by torque (electrical current). Great for grippers where you want to apply a specific gripping force, or for compliant robot arms that should yield when a human pushes them. You command in milliamps (mA).

**`1` — Velocity Control Mode**
The motor spins continuously at a target speed — perfect for wheels on a mobile robot. You command in RPM, or in raw pulses (1 pulse ≈ 0.229 RPM).

**`3` — Position Control Mode** ⭐ *Most common for arms and pan-tilt setups*
Moves the joint to a specific angle, within one full rotation (0–360°). The plugin automatically converts the radians ROS sends into raw pulses the motor understands (roughly 1 pulse = 0.088°).

**`4` — Extended Position Control Mode**
Same idea as mode 3, but allows multi-turn rotation — the pulse count can go beyond a single revolution. Useful for joints with gear reductions, pulleys, or cable drives.

**`5` — Current-based Position Control Mode**
A hybrid of modes 0 and 3. You can target a position *and* set a max torque. Handy for tracked-wheel mechanisms or grippers where you care about both reach and force.

**`16` — PWM Control Mode**
Direct duty cycle control — essentially bypassing all the motor's internal control logic. You're in charge of everything. Rarely needed unless you have a very specific low-level use case.

---

## 3. Per-Motor Configuration — The GPIO Block

This is where the magic happens. The plugin lets you override any register in the motor's Control Table just by putting the exact `Data Name` (case-sensitive, straight from the Dynamixel E-Manual) inside a `<param>` tag.

```xml
<!-- Motor 1 — minimal setup -->
<gpio name="joint1_config">
  <param name="ID">1</param>              <!-- Required: Motor ID, 1–252 -->
  <param name="type">dxl</param>          <!-- Required: Tells the plugin this is a Dynamixel motor -->
  <param name="Operating Mode">3</param>  <!-- Position control: takes radians from ROS, sends pulses to motor -->
  <param name="Torque Enable">1</param>   <!-- 1 = torque on (motor holds position), 0 = motor spins freely -->
</gpio>

<!-- Motor 2 — advanced tuning example -->
<gpio name="joint2_config">
  <param name="ID">2</param>
  <param name="type">dxl</param>
  <param name="Operating Mode">3</param>
  <param name="Torque Enable">1</param>

  <!-- Fine-tuning parameters (units depend on motor series — examples below are for X-Series) -->
  <param name="Profile Velocity">50</param>
  <!-- Limits the max speed during a move. Unit: 0.229 RPM/pulse → 50 ≈ 11.45 RPM -->

  <param name="Profile Acceleration">15</param>
  <!-- Ramp up/down speed. Unit: 214.577 rev/min²/pulse — keeps motion smooth instead of jerky -->

  <param name="Position P Gain">1500</param>
  <!-- Stiffness of the joint (raw Kp value). Higher = stiffer and more resistant to external force,
       but too high and the joint starts oscillating -->

  <param name="Max Position Limit">3000</param>
  <!-- Right-side travel limit. Unit: pulses (0–4095 maps to 0–360°) -->

  <param name="Min Position Limit">1000</param>
  <!-- Left-side travel limit. Prevents the joint from over-rotating and damaging itself -->

  <param name="Current Limit">1193</param>
  <!-- Max current draw. Unit: 2.69 mA/pulse → 1193 ≈ 3.2A. Protects the motor from burning out -->
</gpio>
```

---

## 4. Joint Interfaces — Talking to ROS 2 Controllers

This section wires each physical joint to the ROS 2 control layer. You declare what data each joint can **receive** (command interfaces) and what it **reports back** (state interfaces). Everything uses standard SI units inside ROS:

- `position` → **Radians** (for rotating joints) or **Meters** (for linear joints)
- `velocity` → **Rad/s** or **m/s**
- `effort` → **N·m** (torque) or **N** (force)

```xml
<!-- Joint 1 interface mapping -->
<joint name="joint1">

  <!-- What you can command (write to motor) -->
  <command_interface name="position"/>  <!-- Send target angle in radians (mode 3) -->

  <!-- What you can read back (motor reports to ROS / RViz) -->
  <state_interface name="position"/>   <!-- Current angle in radians -->
  <state_interface name="velocity"/>   <!-- Current speed in rad/s -->
  <state_interface name="effort"/>     <!-- Estimated torque in N·m (derived from current) -->
</joint>

<!-- Joint 2 interface mapping -->
<joint name="joint2">
  <command_interface name="position"/>
  <state_interface name="position"/>
  <state_interface name="velocity"/>
  <state_interface name="effort"/>
</joint>
```

---

## ⚠️ Things That Will Bite You

**Pulse vs. Radian conversion**
Internally, Dynamixel motors work in raw pulses. But ROS 2 and `ros2_control` always use radians externally. The plugin handles the conversion using the `transmission_to_joint_matrix` — you don't need to do the math yourself, but it's good to know it's happening under the hood.

**Typos in parameter names are silent killers**
If you write `torque_enable` instead of `Torque Enable`, the plugin will quietly skip that parameter without any warning. Always copy parameter names character-for-character from the Dynamixel E-Manual.

**Using Current Control for grippers**
If you want a gripper that squeezes at max force until it grabs something, switch `Operating Mode` to `0` and use `<command_interface name="effort"/>` instead of position. That example isn't covered in this guide, but that's the pattern to follow.