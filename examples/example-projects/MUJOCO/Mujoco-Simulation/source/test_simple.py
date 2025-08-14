#!/usr/bin/env python
"""Simple test script to verify container execution."""

import os
import sys

print("=== SIMPLE TEST SCRIPT ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith("FLUIDIZE") or key.startswith("SIMULATION"):
        print(f"  {key}: {value}")

# Test if we can import mujoco
try:
    import mujoco

    print(f"✅ MuJoCo imported successfully: version {mujoco.__version__}")
except Exception as e:
    print(f"❌ Failed to import MuJoCo: {e}")

# Create a simple output file
output_path = os.environ.get("SIMULATION_OUTPUT_PATH", "outputs")
os.makedirs(output_path, exist_ok=True)
test_file = os.path.join(output_path, "test_output.txt")
with open(test_file, "w") as f:
    f.write("Test completed successfully!\n")
print(f"✅ Created test file: {test_file}")

print("=== TEST COMPLETED ===")
