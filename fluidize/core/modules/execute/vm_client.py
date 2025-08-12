"""
VM Execution Client using SSH and safe command construction

This client handles remote VM execution via SSH using properly escaped
commands instead of unsafe string concatenation.
"""

import logging
import shlex
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from fluidize.core.types.execution_models import ContainerSpec, Volume

logger = logging.getLogger(__name__)


@dataclass
class VMExecutionResult:
    """Result of VM command execution."""

    exit_code: int
    stdout: str = ""
    stderr: str = ""
    success: bool = False
    command: str = ""

    def __post_init__(self):
        self.success = self.exit_code == 0


class VMExecutionClient:
    """
    VM execution client using SSH with safe command construction.

    This client builds Docker commands safely using shlex.quote() for
    proper shell escaping, then executes them via SSH.
    """

    def __init__(self, ssh_client=None):
        """
        Initialize VM execution client.

        Args:
            ssh_client: SSH client instance (from paramiko or similar)
        """
        self.ssh_client = ssh_client
        logger.info("VM execution client initialized")

    def run_container(
        self, container_spec: ContainerSpec, volumes: list[Volume], platform: str = "linux/amd64", **kwargs
    ) -> VMExecutionResult:
        """
        Run container on VM using safely constructed Docker command.

        Args:
            container_spec: Container specification
            volumes: Volume specifications
            platform: Docker platform specification
            **kwargs: Additional options

        Returns:
            VMExecutionResult with execution details
        """
        try:
            # Build safe Docker command arguments
            docker_args = self._build_safe_docker_args(container_spec, volumes, platform, **kwargs)

            # Convert to safely quoted command string
            command = " ".join(shlex.quote(arg) for arg in docker_args)

            logger.info(f"Executing Docker command on VM: {container_spec.name}")
            logger.debug(f"Command: {command}")

            # Execute via SSH
            if self.ssh_client:
                return self._execute_via_ssh(command)
            else:
                # For testing or local execution
                return self._execute_locally(docker_args)

        except Exception as e:
            logger.exception("Error running container on VM")
            return VMExecutionResult(exit_code=-1, stderr=str(e), command=command if "command" in locals() else "")

    def run_container_async(
        self, container_spec: ContainerSpec, volumes: list[Volume], platform: str = "linux/amd64", **kwargs
    ) -> str:
        """
        Run container on VM in detached mode.

        Args:
            container_spec: Container specification
            volumes: Volume specifications
            platform: Docker platform specification
            **kwargs: Additional options

        Returns:
            Container ID or job identifier
        """
        # Build command with detached flag
        docker_args = self._build_safe_docker_args(container_spec, volumes, platform, detach=True, **kwargs)

        command = " ".join(shlex.quote(arg) for arg in docker_args)

        logger.info(f"Starting container in background on VM: {container_spec.name}")

        if self.ssh_client:
            # Execute detached command via SSH using Fabric
            result = self.ssh_client.run(command, hide=True, warn=True)
            container_id = result.stdout.strip()
            return container_id
        else:
            # Local execution
            result = subprocess.run(docker_args, capture_output=True, text=True)  # noqa: S603
            return result.stdout.strip()

    def _build_safe_docker_args(
        self,
        container_spec: ContainerSpec,
        volumes: list[Volume],
        platform: str = "linux/amd64",
        detach: bool = False,
        **kwargs,
    ) -> list[str]:
        """
        Build Docker command arguments safely.

        This method constructs docker run arguments as a list,
        which is much safer than string concatenation.
        """
        # For GCS FUSE access on VMs, Docker needs sudo privileges
        args = ["sudo", "docker", "run"]

        # Add basic runtime flags
        self._add_runtime_flags(args, detach, platform)

        # Add container configuration
        self._add_container_config(args, container_spec, volumes, **kwargs)

        # Add image and commands
        args.append(container_spec.image)
        if container_spec.command:
            args.extend(container_spec.command)
        if container_spec.args:
            args.extend(container_spec.args)

        return args

    def _add_runtime_flags(self, args: list[str], detach: bool, platform: str) -> None:
        """Add basic runtime flags to Docker args."""
        if not detach:
            args.append("--rm")  # Remove container when done
        else:
            args.append("-d")  # Detached mode

        if platform:
            args.extend(["--platform", platform])

    def _add_container_config(
        self, args: list[str], container_spec: ContainerSpec, volumes: list[Volume], **kwargs
    ) -> None:
        """Add container configuration to Docker args."""
        # Environment variables
        for key, value in container_spec.env_vars.items():
            args.extend(["-e", f"{key}={value}"])

        # Volume mounts
        docker_volumes = self._convert_volumes_for_vm(volumes, container_spec.volume_mounts)
        for host_path, container_path in docker_volumes.items():
            args.extend(["-v", f"{host_path}:{container_path}"])

        # Working directory
        if container_spec.working_dir:
            args.extend(["--workdir", container_spec.working_dir])

        # Add security, network, and resource configurations
        self._add_security_config(args, container_spec)
        self._add_network_config(args, kwargs)
        self._add_resource_config(args, container_spec)
        self._add_labels(args, container_spec)

    def _add_security_config(self, args: list[str], container_spec: ContainerSpec) -> None:
        """Add security configuration to Docker args."""
        if container_spec.security_context:
            if container_spec.security_context.get("runAsUser"):
                args.extend(["--user", str(container_spec.security_context["runAsUser"])])
            if container_spec.security_context.get("privileged"):
                args.append("--privileged")

    def _add_network_config(self, args: list[str], kwargs: dict) -> None:
        """Add network configuration to Docker args."""
        network_mode = kwargs.get("network_mode", "default")
        if network_mode != "default":
            args.extend(["--network", network_mode])

    def _add_resource_config(self, args: list[str], container_spec: ContainerSpec) -> None:
        """Add resource configuration to Docker args."""
        if container_spec.resources:
            limits = container_spec.resources.get("limits", {})
            if "memory" in limits:
                args.extend(["--memory", limits["memory"]])
            if "cpu" in limits:
                args.extend(["--cpus", limits["cpu"]])

    def _add_labels(self, args: list[str], container_spec: ContainerSpec) -> None:
        """Add labels to Docker args."""
        for key, value in container_spec.labels.items():
            args.extend(["--label", f"{key}={value}"])

    def _convert_volumes_for_vm(self, volumes: list[Volume], mounts: list) -> dict[str, str]:
        """
        Convert volume specifications to VM-appropriate paths.

        For VMs, this typically means GCS FUSE mounts at /mnt/fluidize_users
        """
        volume_mappings = {}

        # Create mapping of volume names to volumes
        volume_map = {vol.name: vol for vol in volumes}

        for mount in mounts:
            if mount.name in volume_map:
                volume = volume_map[mount.name]

                if volume.volume_type == "hostPath":
                    # For VMs, this is typically a GCS FUSE mount
                    host_path = volume.source.get("path", "")
                    volume_mappings[host_path] = mount.mount_path
                elif volume.volume_type == "gcsFuse":
                    # Special handling for GCS FUSE mounts
                    gcs_mount_path = "/mnt/fluidize_users"
                    volume_mappings[gcs_mount_path] = mount.mount_path

        return volume_mappings

    def _execute_via_ssh(self, command: str) -> VMExecutionResult:
        """Execute command via SSH connection using Fabric."""
        try:
            # Execute command using Fabric SSH client
            result = self.ssh_client.run(command, hide=False, warn=True, timeout=3600)

            logger.info(f"SSH command completed with exit code: {result.return_code}")

            return VMExecutionResult(
                exit_code=result.return_code, stdout=result.stdout, stderr=result.stderr, command=command
            )

        except Exception as e:
            logger.exception("SSH execution failed")
            return VMExecutionResult(exit_code=-1, stderr=str(e), command=command)

    def _execute_locally(self, docker_args: list[str]) -> VMExecutionResult:
        """Execute Docker command locally (for testing)."""
        try:
            result = subprocess.run(  # noqa: S603
                docker_args,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            return VMExecutionResult(
                exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr, command=" ".join(docker_args)
            )

        except subprocess.TimeoutExpired:
            return VMExecutionResult(
                exit_code=-1, stderr="Command timed out after 1 hour", command=" ".join(docker_args)
            )
        except Exception as e:
            return VMExecutionResult(exit_code=-1, stderr=str(e), command=" ".join(docker_args))

    def pull_image(self, image: str) -> VMExecutionResult:
        """Pull Docker image on VM."""
        pull_args = ["docker", "pull", image]
        command = " ".join(shlex.quote(arg) for arg in pull_args)

        logger.info(f"Pulling image on VM: {image}")

        if self.ssh_client:
            return self._execute_via_ssh(command)
        else:
            return self._execute_locally(pull_args)

    def get_container_logs(self, container_id: str) -> str:
        """Get logs from a running container."""
        logs_args = ["docker", "logs", container_id]
        command = " ".join(shlex.quote(arg) for arg in logs_args)

        if self.ssh_client:
            result = self._execute_via_ssh(command)
            return result.stdout
        else:
            result = self._execute_locally(logs_args)
            return result.stdout

    def stop_container(self, container_id: str) -> VMExecutionResult:
        """Stop a running container."""
        stop_args = ["docker", "stop", container_id]
        command = " ".join(shlex.quote(arg) for arg in stop_args)

        logger.info(f"Stopping container: {container_id}")

        if self.ssh_client:
            return self._execute_via_ssh(command)
        else:
            return self._execute_locally(stop_args)

    def set_ssh_client(self, ssh_client):
        """Set SSH client for remote execution."""
        self.ssh_client = ssh_client

    def close(self):
        """Close SSH connection if open."""
        if self.ssh_client and hasattr(self.ssh_client, "close"):
            self.ssh_client.close()
