#!/usr/bin/env python
"""
Quick test script for the pinata simulation setup
"""

import os
import sys


def test_imports():
    """Test if all required packages can be imported"""
    try:
        import numpy as np

        print(f"✅ NumPy {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False

    try:
        import matplotlib

        matplotlib.use("Agg")  # Set headless backend
        import matplotlib.pyplot as plt

        print(f"✅ Matplotlib {matplotlib.__version__}")
    except ImportError as e:
        print(f"❌ Matplotlib import failed: {e}")
        return False

    try:
        import seaborn as sns

        print(f"✅ Seaborn {sns.__version__}")
    except ImportError as e:
        print(f"❌ Seaborn import failed: {e}")
        return False

    try:
        import imageio

        print(f"✅ ImageIO {imageio.__version__}")
    except ImportError as e:
        print(f"❌ ImageIO import failed: {e}")
        return False

    try:
        import mujoco

        print(f"✅ MuJoCo {mujoco.__version__}")
    except ImportError as e:
        print(f"❌ MuJoCo import failed: {e}")
        return False

    return True


def test_environment():
    """Test environment setup"""
    print("\n🔍 Environment Check:")
    print(f"Python version: {sys.version}")
    print(f"MUJOCO_GL: {os.environ.get('MUJOCO_GL', 'not set')}")
    print(f"Output path: {os.environ.get('SIMULATION_OUTPUT_PATH', 'not set')}")

    # Test output directory creation
    output_path = os.environ.get("SIMULATION_OUTPUT_PATH", "test_outputs")
    os.makedirs(output_path, exist_ok=True)

    test_file = os.path.join(output_path, "test.txt")
    with open(test_file, "w") as f:
        f.write("Test file created successfully")

    if os.path.exists(test_file):
        print(f"✅ Output directory writable: {output_path}")
        os.remove(test_file)
        return True
    else:
        print(f"❌ Cannot write to output directory: {output_path}")
        return False


def test_mujoco_basic():
    """Test basic MuJoCo functionality"""
    try:
        import mujoco

        # Test basic model creation
        simple_xml = """
        <mujoco>
            <worldbody>
                <geom name="ground" type="plane" size="1 1 0.1"/>
                <body name="box" pos="0 0 0.5">
                    <freejoint/>
                    <geom type="box" size="0.1 0.1 0.1"/>
                </body>
            </worldbody>
        </mujoco>
        """

        model = mujoco.MjModel.from_xml_string(simple_xml)
        data = mujoco.MjData(model)

        # Test forward kinematics
        mujoco.mj_forward(model, data)

        print("✅ MuJoCo basic functionality working")
        return True

    except Exception as e:
        print(f"❌ MuJoCo test failed: {e}")
        return False


def main():
    print("🧪 Testing Pinata Simulation Environment")
    print("=" * 50)

    success = True

    # Test imports
    print("\n📦 Testing imports...")
    if not test_imports():
        success = False

    # Test environment
    print("\n🌍 Testing environment...")
    if not test_environment():
        success = False

    # Test MuJoCo
    print("\n🎯 Testing MuJoCo...")
    if not test_mujoco_basic():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Ready for pinata simulation.")
        return 0
    else:
        print("❌ Some tests failed. Check the environment.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
