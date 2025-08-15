# MuJoCo Simulation Container - With OpenGL support
FROM python:3.9

# Install system dependencies for OpenGL and MuJoCo
RUN apt-get update && apt-get install -y \
    libosmesa6-dev \
    libgl1-mesa-dev \
    libglfw3 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install MuJoCo Python package and dependencies
RUN pip install --no-cache-dir \
    mujoco \
    numpy \
    imageio \
    imageio-ffmpeg \
    matplotlib \
    seaborn

# Set environment variables for MuJoCo
ENV MUJOCO_GL=osmesa
ENV PYTHONPATH=/app/source

# Make sure main.sh will be executable when mounted
RUN mkdir -p /app/node

# Entry point - execute main.sh script
  CMD ["/bin/bash"]
