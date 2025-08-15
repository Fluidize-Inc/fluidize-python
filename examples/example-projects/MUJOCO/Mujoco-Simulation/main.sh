#!/bin/bash

# MuJoCo Simulation Main Execution Script
# This script is executed by the fluidize framework inside the Docker container

set -e  # Exit on any error

echo "Starting MuJoCo Simulation Setup..."

# Python dependencies are already installed in the Docker image
echo "Python dependencies pre-installed in Docker image"

echo "Environment Variables:"
echo "  FLUIDIZE_NODE_PATH: ${FLUIDIZE_NODE_PATH:-not set}"
echo "  FLUIDIZE_SIMULATION_PATH: ${FLUIDIZE_SIMULATION_PATH:-not set}"
echo "  FLUIDIZE_OUTPUT_PATH: ${FLUIDIZE_OUTPUT_PATH:-not set}"
echo "  FLUIDIZE_INPUT_PATH: ${FLUIDIZE_INPUT_PATH:-not set}"

# Set default paths if environment variables are not set
NODE_PATH="${FLUIDIZE_NODE_PATH:-/app}"
SIMULATION_PATH="${FLUIDIZE_SIMULATION_PATH:-/app/source}"
OUTPUT_PATH="${FLUIDIZE_OUTPUT_PATH:-/app/source/outputs}"
INPUT_PATH="${FLUIDIZE_INPUT_PATH:-}"

echo "Using paths:"
echo "  Node path: $NODE_PATH"
echo "  Simulation path: $SIMULATION_PATH"
echo "  Output path: $OUTPUT_PATH"
echo "  Input path: $INPUT_PATH"

# Ensure output directory exists
mkdir -p "$OUTPUT_PATH"

# Change to simulation directory
cd "$SIMULATION_PATH"

# Set MuJoCo environment variables for headless rendering
export MUJOCO_GL=osmesa
export PYTHONPATH="$SIMULATION_PATH:$PYTHONPATH"

# Export paths for the Python script
export SIMULATION_OUTPUT_PATH="$OUTPUT_PATH"
export SIMULATION_INPUT_PATH="$INPUT_PATH"

# Run the MuJoCo simulation
echo "Executing pinata simulation..."
python pinata_simulation.py

# Check if simulation was successful
if [ $? -eq 0 ]; then
    echo "MuJoCo simulation completed successfully!"
    echo "Output files generated in: $OUTPUT_PATH"
    ls -la "$OUTPUT_PATH"
    exit 0  # Explicitly exit with success code
else
    echo "MuJoCo simulation failed!"
    exit 1
fi
