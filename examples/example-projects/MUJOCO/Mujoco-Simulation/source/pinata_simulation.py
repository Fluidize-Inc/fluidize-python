#!/usr/bin/env python
"""
MuJoCo Pinata Simulation with Tendons, Actuators, and Sensors
Enhanced version with professional visualization and Docker compatibility
"""

import os
import sys
from datetime import datetime

# Set matplotlib backend for headless operation
import matplotlib
import numpy as np

matplotlib.use("Agg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

try:
    import imageio
    import mujoco

    print(f"✅ MuJoCo version: {mujoco.__version__}")
    print("✅ ImageIO available for video generation")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Set professional plot style
plt.style.use("seaborn-v0_8" if "seaborn-v0_8" in plt.style.available else "default")
sns.set_palette("husl")


class PinataSimulation:
    """
    Enhanced MuJoCo Pinata simulation with professional visualization
    """

    def __init__(self, output_path=None):
        """Initialize the simulation with output path configuration"""
        self.output_path = output_path or os.environ.get("SIMULATION_OUTPUT_PATH", "outputs")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directories
        self.video_dir = os.path.join(self.output_path, "videos")
        self.plot_dir = os.path.join(self.output_path, "plots")
        self.data_dir = os.path.join(self.output_path, "data")
        self.log_dir = os.path.join(self.output_path, "logs")

        for directory in [self.video_dir, self.plot_dir, self.data_dir, self.log_dir]:
            os.makedirs(directory, exist_ok=True)

        # Simulation parameters
        self.duration = 3.0  # seconds
        self.framerate = 60  # Hz
        self.video_width = 1280
        self.video_height = 720

        # Data storage
        self.times = []
        self.sensor_data = []
        self.positions = []
        self.velocities = []
        self.bat_angles = []
        self.tendon_lengths = []

        print("🎯 Pinata Simulation initialized")
        print(f"📁 Output path: {self.output_path}")
        print(f"🕒 Timestamp: {self.timestamp}")

    def create_mjcf_model(self):
        """Create the MJCF XML model for the pinata simulation"""
        mjcf_xml = """
        <mujoco model="pinata_simulation">
          <compiler angle="radian"/>

          <option timestep="0.002" integrator="RK4">
            <flag contact="enable" energy="enable"/>
          </option>

          <asset>
            <texture name="grid" type="2d" builtin="checker" rgb1=".2 .3 .4"
             rgb2=".3 .4 .5" width="300" height="300" mark="none"/>
            <material name="grid" texture="grid" texrepeat="2 2"
             texuniform="true" reflectance=".3"/>
            <material name="bat" rgba="0.6 0.3 0.1 1"/>
            <material name="pinata" rgba="1 0.8 0.2 1"/>
          </asset>

          <visual>
            <global offwidth="1280" offheight="720"/>
            <quality shadowsize="2048" offsamples="4"/>
            <map force="0.1" shadowclip="1"/>
            <scale forcewidth="0.05" contactwidth="0.1" contactheight="0.02"
             connect="0.2" com="0.3" selectpoint="0.1" jointlength="0.1" jointwidth="0.05"/>
          </visual>

          <worldbody>
            <light name="sun" pos="0 0 2" dir="0 0 -1" diffuse="1 1 1"/>
            <light name="spot" pos="0.5 -0.5 1.5" dir="-0.5 0.5 -1" diffuse="0.8 0.8 0.8"/>

            <geom name="floor" type="plane" pos="0 0 -0.5" size="3 3 0.1"
             material="grid" solimp="0.99 0.99 0.01" solref="0.001 1"/>

            <site name="anchor" pos="0 0 .3" size=".01"/>

            <camera name="fixed" pos="0 -1.3 .5" xyaxes="1 0 0 0 1 2"/>

            <!-- Bat assembly - EXACT tutorial setup -->
            <geom name="pole" type="cylinder" fromto=".3 0 -.5 .3 0 -.1" size=".04"/>
            <body name="bat" pos=".3 0 -.1">
              <joint name="swing" type="hinge" damping="1" axis="0 0 1"/>
              <geom name="bat" type="capsule" fromto="0 0 .04 0 -.3 .04"
               size=".04" rgba="0 0 1 1"/>
            </body>

            <!-- Pinata (box and sphere) -->
            <body name="box_and_sphere" pos="0 0 0">
              <joint name="free" type="free"/>
              <geom name="red_box" type="box" size=".1 .1 .1" rgba="1 0 0 1"/>
              <geom name="green_sphere" size=".06" pos=".1 .1 .1" rgba="0 1 0 1"/>
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
        return mjcf_xml

    def setup_simulation(self):
        """Initialize the MuJoCo model and data structures"""
        print("🔧 Setting up simulation...")

        # Create model from XML
        mjcf_xml = self.create_mjcf_model()
        self.model = mujoco.MjModel.from_xml_string(mjcf_xml)
        self.data = mujoco.MjData(self.model)

        # Setup visualization options - clean view without force arrows
        self.vis_options = mujoco.MjvOption()
        self.vis_options.flags[mujoco.mjtVisFlag.mjVIS_TENDON] = True  # Keep tendon visible

        print(f"📊 Model loaded: {self.model.ngeom} geoms, {self.model.nbody} bodies")
        print(f"🎛️  Actuators: {self.model.nu}, Sensors: {self.model.nsensor}")

    def control_strategy(self, time):
        """Define control strategy for the bat motor - parameterized for tuning"""
        # Constant actuator signal - parameterized for tuning
        return {{motor_strength}}

    def collect_data(self):
        """Collect sensor and state data during simulation"""
        self.times.append(self.data.time)

        # Sensor data - simplified to match tutorial
        accel_data = self.data.sensor("accelerometer").data.copy()

        # Get bat joint position and velocity directly
        bat_pos = self.data.joint("swing").qpos[0] if hasattr(self.data.joint("swing"), "qpos") else 0.0
        bat_vel = self.data.joint("swing").qvel[0] if hasattr(self.data.joint("swing"), "qvel") else 0.0

        # Calculate wire length from tendon
        wire_len = self.data.tendon("wire").length[0] if hasattr(self.data.tendon("wire"), "length") else 0.0

        sensor_reading = {
            "accel": accel_data,
            "gyro": np.zeros(3),  # No gyro in simplified version
            "bat_pos": bat_pos,
            "bat_vel": bat_vel,
            "wire_length": wire_len,
        }
        self.sensor_data.append(sensor_reading)

        # Kinematic data
        pinata_pos = self.data.body("box_and_sphere").xpos.copy()
        pinata_vel = self.data.body("box_and_sphere").cvel.copy()

        self.positions.append(pinata_pos)
        self.velocities.append(pinata_vel)
        self.bat_angles.append(bat_pos)
        self.tendon_lengths.append(wire_len)

    def run_simulation(self):
        """Execute the main simulation loop"""
        print("🚀 Starting simulation...")

        # Reset and initialize - exactly like tutorial
        mujoco.mj_resetData(self.model, self.data)

        frames = []
        n_frames = int(self.duration * self.framerate)

        with mujoco.Renderer(self.model, self.video_height, self.video_width) as renderer:
            step_count = 0
            last_frame_time = 0

            while self.data.time < self.duration:
                # Control signal
                control_signal = self.control_strategy(self.data.time)
                self.data.ctrl[0] = control_signal

                # Step simulation
                mujoco.mj_step(self.model, self.data)
                step_count += 1

                # Collect data every timestep
                self.collect_data()

                # Render frame
                if len(frames) < self.data.time * self.framerate:
                    mujoco.mj_forward(self.model, self.data)
                    renderer.update_scene(self.data, camera="fixed", scene_option=self.vis_options)
                    pixels = renderer.render()
                    frames.append(pixels)
                    last_frame_time = self.data.time

                # Progress indicator
                if step_count % 1000 == 0:
                    progress = (self.data.time / self.duration) * 100
                    print(f"⏳ Progress: {progress:.1f}% (t={self.data.time:.2f}s)")

        print(f"✅ Simulation completed: {len(frames)} frames, {step_count} steps")
        return frames

    def create_video(self, frames):
        """Generate MP4 video from simulation frames"""
        print("🎬 Creating video...")

        video_filename = f"pinata_simulation_{self.timestamp}.mp4"
        video_path = os.path.join(self.video_dir, video_filename)

        # Write video with high quality settings
        imageio.mimsave(
            video_path,
            frames,
            fps=self.framerate,
            codec="libx264",
            quality=8,
            macro_block_size=1,
            ffmpeg_params=["-preset", "slow", "-crf", "18"],
        )

        print(f"📹 Video saved: {video_path}")
        return video_path

    def create_plots(self):
        """Generate comprehensive analysis plots"""
        print("📊 Creating analysis plots...")

        # Convert data to numpy arrays
        times = np.array(self.times)
        positions = np.array(self.positions)
        velocities = np.array(self.velocities)

        # Extract sensor data
        accel_x = [s["accel"][0] for s in self.sensor_data]
        accel_y = [s["accel"][1] for s in self.sensor_data]
        accel_z = [s["accel"][2] for s in self.sensor_data]
        bat_angles = [s["bat_pos"] for s in self.sensor_data]
        wire_lengths = [s["wire_length"] for s in self.sensor_data]

        # Create comprehensive plot
        fig = plt.figure(figsize=(16, 12), dpi=150)
        gs = GridSpec(4, 2, figure=fig, hspace=0.3, wspace=0.25)

        # Accelerometer data
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(times, accel_x, "r-", label="X-axis", linewidth=2, alpha=0.8)
        ax1.plot(times, accel_y, "g-", label="Y-axis", linewidth=2, alpha=0.8)
        ax1.plot(times, accel_z, "b-", label="Z-axis", linewidth=2, alpha=0.8)
        ax1.set_title("IMU Accelerometer Data", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Acceleration (m/s²)", fontsize=12)
        ax1.legend(loc="upper right")
        ax1.grid(True, alpha=0.3)

        # Position tracking
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.plot(times, positions[:, 0], "r-", label="X", linewidth=2)
        ax2.plot(times, positions[:, 1], "g-", label="Y", linewidth=2)
        ax2.plot(times, positions[:, 2], "b-", label="Z", linewidth=2)
        ax2.set_title("Pinata Position", fontsize=14, fontweight="bold")
        ax2.set_ylabel("Position (m)", fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Bat angle and wire length
        ax3 = fig.add_subplot(gs[1, 1])
        ax3_twin = ax3.twinx()
        line1 = ax3.plot(times, bat_angles, "purple", linewidth=2, label="Bat Angle")
        line2 = ax3_twin.plot(times, wire_lengths, "orange", linewidth=2, label="Wire Length")
        ax3.set_title("Bat Motion & Wire Length", fontsize=14, fontweight="bold")
        ax3.set_ylabel("Bat Angle (rad)", fontsize=12, color="purple")
        ax3_twin.set_ylabel("Wire Length (m)", fontsize=12, color="orange")
        ax3.grid(True, alpha=0.3)

        # Phase plot (X-Y position)
        ax4 = fig.add_subplot(gs[2, 0])
        scatter = ax4.scatter(positions[:, 0], positions[:, 1], c=times, cmap="viridis", s=10, alpha=0.7)
        ax4.set_title("Position Phase Plot (X-Y)", fontsize=14, fontweight="bold")
        ax4.set_xlabel("X Position (m)", fontsize=12)
        ax4.set_ylabel("Y Position (m)", fontsize=12)
        ax4.grid(True, alpha=0.3)
        cbar = plt.colorbar(scatter, ax=ax4)
        cbar.set_label("Time (s)", fontsize=10)

        # Energy analysis
        ax5 = fig.add_subplot(gs[2, 1])
        # Calculate kinetic energy (approximate)
        kinetic_energy = 0.5 * 0.7 * np.sum(velocities[:, :3] ** 2, axis=1)  # mass * v²
        potential_energy = 0.7 * 9.81 * positions[:, 2]  # m * g * h
        total_energy = kinetic_energy + potential_energy

        ax5.plot(times, kinetic_energy, "r-", label="Kinetic", linewidth=2)
        ax5.plot(times, potential_energy, "b-", label="Potential", linewidth=2)
        ax5.plot(times, total_energy, "k--", label="Total", linewidth=2)
        ax5.set_title("Energy Analysis", fontsize=14, fontweight="bold")
        ax5.set_ylabel("Energy (J)", fontsize=12)
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # Spectral analysis of acceleration
        ax6 = fig.add_subplot(gs[3, :])
        accel_magnitude = np.sqrt(np.array(accel_x) ** 2 + np.array(accel_y) ** 2 + np.array(accel_z) ** 2)

        # Compute FFT
        dt = times[1] - times[0]
        freqs = np.fft.fftfreq(len(accel_magnitude), dt)[: len(accel_magnitude) // 2]
        fft_magnitude = np.abs(np.fft.fft(accel_magnitude))[: len(accel_magnitude) // 2]

        ax6.plot(freqs, fft_magnitude, "navy", linewidth=2)
        ax6.set_title("Acceleration Frequency Spectrum", fontsize=14, fontweight="bold")
        ax6.set_xlabel("Frequency (Hz)", fontsize=12)
        ax6.set_ylabel("Magnitude", fontsize=12)
        ax6.set_xlim(0, 10)  # Focus on low frequencies
        ax6.grid(True, alpha=0.3)

        plt.suptitle(f"Pinata Simulation Analysis - {self.timestamp}", fontsize=16, fontweight="bold", y=0.98)

        # Save plot
        plot_filename = f"comprehensive_analysis_{self.timestamp}.png"
        plot_path = os.path.join(self.plot_dir, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
        plt.close()

        print(f"📈 Plot saved: {plot_path}")
        return plot_path

    def save_data(self):
        """Save simulation data to files"""
        print("💾 Saving data...")

        # Prepare data dictionary
        data_dict = {
            "times": np.array(self.times),
            "positions": np.array(self.positions),
            "velocities": np.array(self.velocities),
            "accelerometer": np.array([s["accel"] for s in self.sensor_data]),
            "gyroscope": np.array([s["gyro"] for s in self.sensor_data]),
            "bat_angles": np.array([s["bat_pos"] for s in self.sensor_data]),
            "wire_lengths": np.array([s["wire_length"] for s in self.sensor_data]),
            "simulation_params": {
                "duration": self.duration,
                "timestep": self.model.opt.timestep,
                "framerate": self.framerate,
            },
        }

        # Save as NPZ
        npz_filename = f"simulation_data_{self.timestamp}.npz"
        npz_path = os.path.join(self.data_dir, npz_filename)
        np.savez_compressed(npz_path, **data_dict)

        # Save as CSV for easy access
        csv_data = {
            "time": self.times,
            "pos_x": [p[0] for p in self.positions],
            "pos_y": [p[1] for p in self.positions],
            "pos_z": [p[2] for p in self.positions],
            "accel_x": [s["accel"][0] for s in self.sensor_data],
            "accel_y": [s["accel"][1] for s in self.sensor_data],
            "accel_z": [s["accel"][2] for s in self.sensor_data],
            "bat_angle": [s["bat_pos"] for s in self.sensor_data],
            "wire_length": [s["wire_length"] for s in self.sensor_data],
        }

        import csv

        csv_filename = f"sensor_data_{self.timestamp}.csv"
        csv_path = os.path.join(self.data_dir, csv_filename)

        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_data.keys())
            writer.writeheader()
            for i in range(len(self.times)):
                row = {key: values[i] for key, values in csv_data.items()}
                writer.writerow(row)

        print(f"💾 Data saved: {npz_path}")
        print(f"📊 CSV saved: {csv_path}")
        return npz_path, csv_path

    def generate_summary_log(self, video_path, plot_path, data_paths):
        """Generate a summary log of the simulation"""
        log_filename = f"simulation_log_{self.timestamp}.txt"
        log_path = os.path.join(self.log_dir, log_filename)

        with open(log_path, "w") as f:
            f.write("MuJoCo Pinata Simulation Log\n")
            f.write(f"{'=' * 50}\n")
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"Duration: {self.duration:.2f} seconds\n")
            f.write(f"Total data points: {len(self.times)}\n")
            f.write(f"Average timestep: {np.mean(np.diff(self.times)):.4f} seconds\n")
            f.write(f"Video file: {video_path}\n")
            f.write(f"Plot file: {plot_path}\n")
            f.write(f"Data files: {', '.join(data_paths)}\n")
            f.write("\nSimulation Statistics:\n")
            f.write(f"Max acceleration: {np.max([np.linalg.norm(s['accel']) for s in self.sensor_data]):.2f} m/s²\n")
            f.write(f"Max bat angle: {np.max(self.bat_angles):.3f} rad\n")
            f.write(f"Wire length range: {np.min(self.tendon_lengths):.3f} - {np.max(self.tendon_lengths):.3f} m\n")

        print(f"📋 Log saved: {log_path}")
        return log_path


def main():
    """Main execution function"""
    print("🎭 Starting MuJoCo Pinata Simulation")
    print("=" * 50)

    # Check environment
    print(f"🐍 Python: {sys.version}")
    print(f"🔧 MuJoCo GL: {os.environ.get('MUJOCO_GL', 'not set')}")
    print(f"📁 Output path: {os.environ.get('SIMULATION_OUTPUT_PATH', 'default')}")

    try:
        # Initialize simulation
        sim = PinataSimulation()

        # Setup
        sim.setup_simulation()

        # Run simulation
        frames = sim.run_simulation()

        # Generate outputs
        video_path = sim.create_video(frames)
        plot_path = sim.create_plots()
        data_paths = sim.save_data()
        log_path = sim.generate_summary_log(video_path, plot_path, data_paths)

        # Final summary
        print("\n🎉 Simulation completed successfully!")
        print("📂 Generated files:")
        print(f"   📹 Video: {video_path}")
        print(f"   📊 Plots: {plot_path}")
        print(f"   💾 Data: {', '.join(data_paths)}")
        print(f"   📋 Log: {log_path}")

        return 0

    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
