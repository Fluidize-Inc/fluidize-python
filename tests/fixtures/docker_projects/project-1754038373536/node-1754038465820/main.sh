#!/bin/bash

# Test2 Duplicate Node Script

echo "=== Test2 Duplicate Node ==="
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "=== Environment Variables ==="
echo "Node ID: ${FLUIDIZE_NODE_ID}"
echo "Input Path: ${FLUIDIZE_INPUT_PATH:-/mnt/inputs}"
echo "Output Path: ${FLUIDIZE_OUTPUT_PATH:-/mnt/outputs}"
echo "Execution Mode: ${FLUIDIZE_EXECUTION_MODE}"

echo "=== Starting Test2 execution ==="
# Run the Python script with environment variable paths (with fallback to hardcoded paths)
python main.py "${FLUIDIZE_INPUT_PATH:-/mnt/inputs}" "${FLUIDIZE_OUTPUT_PATH:-/mnt/outputs}"

echo "=== Test2 execution completed successfully ==="
