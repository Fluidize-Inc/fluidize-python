"""
Script to run the MuJoCo simulation using FluidizeClient.

This script demonstrates how to use the fluidize client to execute
the cartpole parameter tuning simulation.
"""

from fluidize import FluidizeClient
from fluidize.core.types.runs import RunFlowPayload


def main():
    """Run the MuJoCo cartpole simulation."""
    print("🚀 Starting MuJoCo Simulation via Fluidize Client")
    print("=" * 60)

    try:
        # Initialize client in local mode
        print("📦 Initializing FluidizeClient in local mode...")
        client = FluidizeClient(mode="local")
        print(f"✅ Client initialized: {client}")

        # Get the MUJOCO project
        print("\n📁 Getting MUJOCO project...")
        project = client.projects.get("MUJOCO")
        print(f"✅ Project found: {project}")

        # Create run payload
        payload = RunFlowPayload(
            name="MuJoCo Cartpole Parameter Tuning Demo",
            description="Cartpole balancing simulation testing different control gain parameters to demonstrate parameter tuning effects",
            tags=["mujoco", "cartpole", "parameter-tuning", "control-systems", "demo"],
        )
        print(f"\n🎯 Payload created: {payload.name}")

        # Run the flow
        print("\n🏃 Starting simulation flow...")
        result = project.runs.run_flow(payload)
        print(f"✅ Flow execution result: {result}")

        print("\n" + "=" * 60)
        print("🎉 MuJoCo simulation flow started successfully!")
        print(f"📊 Flow Status: {result.get('flow_status', 'Unknown')}")
        print(f"🔢 Run Number: {result.get('run_number', 'Unknown')}")
        print("\n💡 The simulation will:")
        print("   • Test 4 different control gain values (5.0, 10.0, 20.0, 50.0)")
        print("   • Generate MP4 videos showing cartpole behavior for each gain")
        print("   • Create comparison plots showing performance vs parameters")
        print("   • Save structured results to JSON")
        print("\n📁 Check the output directory for results:")
        print(f"   {project._project_summary.location}/Mujoco-Simulation/source/outputs/")

    except Exception as e:
        print(f"❌ Error running simulation: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("   • Ensure Docker is running and accessible")
        print("   • Check that the MUJOCO project exists in ~/.fluidize/projects/")
        print("   • Verify the project structure is correct")
        raise


if __name__ == "__main__":
    main()
