import subprocess
from typing import Optional

from fluidize.core.modules.logging.process_executor import ProcessExecutor
from fluidize.core.modules.run.node.methods.base.Execute import BaseExecutionManager
from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import ContainerPaths, NodePaths


class LocalExecutionManager(BaseExecutionManager):
    def __init__(
        self,
        node: nodeProperties_simulation,
        prev_node: Optional[nodeProperties_simulation],
        project: ProjectSummary,
        run_id: Optional[str] = None,
    ) -> None:
        super().__init__(node, prev_node, project)
        self.run_id = run_id

    def print_job_info(self) -> None:
        """Log information about the job being executed"""
        pass

    def pull_docker_image(self) -> bool:
        """Pull the Docker image required for the simulation"""
        pull_cmd = f"docker pull {self.node.container_image}"

        try:
            subprocess.run(pull_cmd, shell=True, check=True)  # noqa: S602
        except subprocess.CalledProcessError:
            return False
        return True

    def _set_input_mount_args(self, node_paths: NodePaths, container_paths: ContainerPaths) -> str:
        """Set the input mount arguments for the Docker run command"""
        if node_paths.input_path:
            return f"-v {node_paths.input_path}:{container_paths.input_path}"
        return ""

    def _build_environment_vars(self, node_paths: NodePaths, container_paths: ContainerPaths) -> dict[str, str]:
        """Build environment variables for consistent path handling across local and cloud"""
        env_vars = {
            "FLUIDIZE_NODE_ID": str(self.node.node_id),
            "FLUIDIZE_NODE_PATH": str(container_paths.node_path),
            "FLUIDIZE_SIMULATION_PATH": str(container_paths.simulation_path),
            "FLUIDIZE_OUTPUT_PATH": str(container_paths.output_path),
            "FLUIDIZE_EXECUTION_MODE": "local_docker",
        }

        # Only set input path if there's a previous node
        if container_paths.input_path:
            env_vars["FLUIDIZE_INPUT_PATH"] = str(container_paths.input_path)

        return env_vars

    def run_container(self, node_paths: NodePaths, container_paths: ContainerPaths) -> tuple[str, bool]:
        """Run the Docker container with the simulation"""

        self.input_mount_args = self._set_input_mount_args(node_paths, container_paths)

        # Add output mount for proper file saving
        output_mount_args = f"-v {node_paths.output_path}:{container_paths.output_path}"

        # Build environment variables for consistent path handling
        env_vars = self._build_environment_vars(node_paths, container_paths)
        env_args = " ".join([f"-e {key}={value}" for key, value in env_vars.items()])

        # Run the Docker container with WORKDIR approach
        docker_cmd = (
            f"docker run --rm "
            f"-v {node_paths.node_path}:{container_paths.node_path} "
            f"{self.input_mount_args} "
            f"{output_mount_args} "
            f"{env_args} "
            f"--workdir {container_paths.simulation_path} "
            f"--entrypoint /bin/bash "
            f"{self.node.container_image} "
            f"{container_paths.node_path}/main.sh"
        )

        # Use ProcessExecutor for clean command execution with logging
        executor = ProcessExecutor(self.run_id, str(self.node.node_id))
        return executor.execute_with_logging(docker_cmd, f"Docker execution: {self.node.container_image}")

    def _execute_node(self) -> str:
        """Main execution method that orchestrates the whole process"""
        self.print_job_info()

        if not self.pull_docker_image():
            return "failure: docker pull failed"

        result, _ = self.run_container(node_paths=self.node_paths, container_paths=self.container_paths)

        return result
