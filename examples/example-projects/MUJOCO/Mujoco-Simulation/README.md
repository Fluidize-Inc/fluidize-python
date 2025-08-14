# MuJoCo Pinata Simulation

Enhanced implementation of the "Tendons, actuators and sensors" example from the MuJoCo tutorial with professional visualization and Docker compatibility.

## Overview

This simulation features:
- **Pinata**: A compound object (box + sphere) suspended by a tendon
- **Bat**: Motor-controlled bat that swings to hit the pinata
- **Sensors**: IMU (accelerometer + gyroscope) to measure pinata motion
- **Enhanced Visualization**: High-quality video output and publication-ready plots

## Features

### Simulation Components
- Spatial tendon with realistic physics
- Motor actuator with sinusoidal control
- Multi-body pinata with realistic dynamics
- Comprehensive sensor suite (IMU, joint sensors, tendon length)

### Outputs
- **MP4 Video**: High-quality 1280x720 @ 60fps with contact visualization
- **Analysis Plots**: Multi-panel scientific plots with:
  - Accelerometer time series (3-axis)
  - Position tracking and phase plots
  - Energy analysis (kinetic/potential)
  - Frequency spectrum analysis
  - Bat motion and wire length correlation
- **Data Export**: Both NPZ (binary) and CSV formats for easy analysis
- **Comprehensive Logging**: Simulation parameters and statistics

### Enhanced Visualization
- Contact points and force vectors
- Tendon visualization
- Professional matplotlib styling with Seaborn
- Multiple camera views
- Anti-aliased rendering

## Running the Simulation

### Docker (Recommended)
```bash
docker run -v $(pwd):/app mujoco-simulation:latest
```

The simulation will automatically:
1. Create output directories (`source/outputs/`)
2. Run the pinata simulation
3. Generate all visualization and data files
4. Print a summary of created files

### Expected Outputs
```
source/outputs/
├── videos/
│   └── pinata_simulation_[timestamp].mp4
├── plots/
│   └── comprehensive_analysis_[timestamp].png
├── data/
│   ├── simulation_data_[timestamp].npz
│   └── sensor_data_[timestamp].csv
└── logs/
    └── simulation_log_[timestamp].txt
```

## Technical Details

### Model Specifications
- **Physics**: RK4 integrator with 2ms timestep
- **Rendering**: OpenGL with anti-aliasing and shadows
- **Contact**: Realistic contact dynamics with visualization
- **Materials**: Custom textures and lighting

### Data Collection
- Full 6-DOF IMU data (acceleration + angular velocity)
- Pinata position and velocity tracking
- Bat joint angles and velocities
- Tendon length measurements
- Energy calculations

### Analysis Features
- Time-domain analysis of all sensor channels
- Frequency-domain analysis (FFT) of acceleration
- Phase space plots for trajectory analysis
- Energy conservation tracking
- Statistical summaries

## Dependencies

All dependencies are pre-installed in the Docker container:
- `mujoco` - Physics simulation
- `numpy` - Numerical computing
- `matplotlib` - Plotting
- `seaborn` - Enhanced plot styling
- `imageio` - Video generation
- `imageio-ffmpeg` - MP4 encoding

## Files

- `pinata_simulation.py` - Main simulation script
- `test_pinata.py` - Environment validation script
- `main.sh` - Docker entry point
- `Dockerfile` - Container specification

## Customization

Key parameters can be modified in the `PinataSimulation` class:
- `duration` - Simulation time (default: 3.0s)
- `framerate` - Video framerate (default: 60 fps)
- `video_width/height` - Resolution (default: 1280x720)
- Control strategy in `control_strategy()` method

## Scientific Applications

This simulation demonstrates:
- Multi-body dynamics with constraints
- Sensor fusion and data analysis
- Contact mechanics visualization
- Control system implementation
- Real-time physics simulation
- Scientific data visualization

Perfect for education, research, and demonstration of advanced physics simulation capabilities.
