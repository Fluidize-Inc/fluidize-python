#!/usr/bin/env python
"""Debug script to test the exact tutorial MJCF"""

import os

import mujoco

# Set environment for headless rendering
os.environ["MUJOCO_GL"] = "osmesa"

# EXACT tutorial MJCF from your message
MJCF = """
<mujoco>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1=".1 .2 .3"
     rgb2=".2 .3 .4" width="300" height="300" mark="none"/>
    <material name="grid" texture="grid" texrepeat="1 1"
     texuniform="true" reflectance=".2"/>
  </asset>

  <worldbody>
    <light name="light" pos="0 0 1"/>
    <geom name="floor" type="plane" pos="0 0 -.5" size="2 2 .1" material="grid"/>
    <site name="anchor" pos="0 0 .3" size=".01"/>
    <camera name="fixed" pos="0 -1.3 .5" xyaxes="1 0 0 0 1 2"/>

    <geom name="pole" type="cylinder" fromto=".3 0 -.5 .3 0 -.1" size=".04"/>
    <body name="bat" pos=".3 0 -.1">
      <joint name="swing" type="hinge" damping="1" axis="0 0 1"/>
      <geom name="bat" type="capsule" fromto="0 0 .04 0 -.3 .04"
       size=".04" rgba="0 0 1 1"/>
    </body>

    <body name="box_and_sphere" pos="0 0 0">
      <joint name="free" type="free"/>
      <geom name="red_box" type="box" size=".1 .1 .1" rgba="1 0 0 1"/>
      <geom name="green_sphere"  size=".06" pos=".1 .1 .1" rgba="0 1 0 1"/>
      <site name="hook" pos="-.1 -.1 -.1" size=".01"/>
      <site name="IMU"/>
    </body>
  </worldbody>

  <tendon>
    <spatial name="wire" limited="true" range="0 0.35" width="0.003">
      <site site="anchor"/>
      <site site="hook"/>
    </spatial>
  </tendon>

  <actuator>
    <motor name="my_motor" joint="swing" gear="1"/>
  </actuator>

  <sensor>
    <accelerometer name="accelerometer" site="IMU"/>
  </sensor>
</mujoco>
"""


def main():
    print("🧪 Testing exact tutorial MJCF...")

    try:
        model = mujoco.MjModel.from_xml_string(MJCF)
        data = mujoco.MjData(model)

        print("✅ Model created successfully")
        print(f"📊 Bodies: {model.nbody}, Geoms: {model.ngeom}")
        print(f"🔗 Tendons: {model.ntendon}")

        # Reset and step forward to see initial state
        mujoco.mj_resetData(model, data)
        mujoco.mj_forward(model, data)

        print(f"Initial pinata position: {data.body('box_and_sphere').xpos}")
        print(f"Initial wire length: {data.tendon('wire').length[0]:.3f}m")

        # Step simulation a few times to see if pinata falls
        data.ctrl = 20  # Set motor control

        for i in range(100):
            mujoco.mj_step(model, data)
            if i % 20 == 0:
                pos = data.body("box_and_sphere").xpos
                wire_len = data.tendon("wire").length[0]
                print(f"Step {i:3d}: pinata z={pos[2]:.3f}, wire_len={wire_len:.3f}")

        final_pos = data.body("box_and_sphere").xpos
        print(f"\nFinal pinata position: {final_pos}")

        if final_pos[2] < -0.4:
            print("❌ PINATA FELL TO GROUND!")
        else:
            print("✅ Pinata stayed suspended")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
