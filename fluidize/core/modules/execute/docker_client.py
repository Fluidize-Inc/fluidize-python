"""
Docker Execution Client using Docker SDK

This client handles Docker container execution using the official Docker SDK
instead of constructing command strings. Much safer and more robust.
"""

import logging
from dataclasses import dataclass
from typing import Optional

try:
    import docker  # type: ignore[import-untyped]
    from docker.errors import ContainerError, DockerException, ImageNotFound  # type: ignore[import-untyped]
    from docker.models.containers import Container  # type: ignore[import-untyped]
except ImportError:
    docker = None

from fluidize.core.types.execution_models import ContainerSpec, Volume

logger = logging.getLogger(__name__)


class DockerSDKMissingError(ImportError):
    """Raised when Docker SDK is not available."""

    def __init__(self) -> None:
        super().__init__("Docker SDK not available. Install with: pip install docker")


@dataclass
class ContainerResult:
    """Result of container execution."""

    exit_code: int
    stdout: str = ""
    stderr: str = ""
    container_id: Optional[str] = None
    success: bool = False

    def __post_init__(self) -> None:
        self.success = self.exit_code == 0


class DockerExecutionClient:
    """
    Docker execution client using Docker SDK for Python.

    This client provides type-safe, secure Docker container execution
    without the risks of command string construction.
    """

    def __init__(self) -> None:
        """Initialize Docker client."""
        if docker is None:
            raise DockerSDKMissingError()

        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except DockerException:
            logger.exception("Failed to initialize Docker client")
            raise

    def pull_image(self, image: str) -> bool:
        """
        Pull Docker image if not present locally.

        Args:
            image: Docker image name

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling Docker image: {image}")
            self.client.images.pull(image)
            logger.info(f"Successfully pulled image: {image}")
        except ImageNotFound:
            logger.exception(f"Image not found: {image}")
            return False
        except DockerException:
            logger.exception(f"Failed to pull image {image}")
            return False
        else:
            return True

    def run_container(self, container_spec: ContainerSpec, volumes: list[Volume], **kwargs: str) -> ContainerResult:
        """
        Run container using Docker SDK.

        Args:
            container_spec: Container specification
            volumes: Volume specifications
            **kwargs: Additional docker run options

        Returns:
            ContainerResult with execution details
        """
        try:
            # Convert volumes to Docker SDK format
            docker_volumes = self._convert_volumes(volumes, container_spec.volume_mounts)

            # Build run arguments
            run_kwargs = {
                "image": container_spec.image,
                "command": self._build_command(container_spec),
                "environment": container_spec.env_vars,
                "volumes": docker_volumes,
                "working_dir": container_spec.working_dir,
                "remove": True,  # Auto-remove container when done
                "detach": False,  # Wait for completion
                "stdout": True,
                "stderr": True,
                **kwargs,
            }

            # Add security context if provided
            if container_spec.security_context:
                self._apply_security_context(run_kwargs, container_spec.security_context)

            logger.info(f"Running container: {container_spec.name}")
            logger.debug(f"Container run args: {run_kwargs}")

            # Run container
            container_output = self.client.containers.run(**run_kwargs)

            # Handle output
            if isinstance(container_output, bytes):
                stdout = container_output.decode("utf-8")
                stderr = ""
            elif isinstance(container_output, Container):
                # If detached, get logs
                logs = container_output.logs(stdout=True, stderr=True)
                stdout = logs.decode("utf-8") if isinstance(logs, bytes) else str(logs)
                stderr = ""
            else:
                stdout = str(container_output)
                stderr = ""

            logger.info(f"Container {container_spec.name} completed successfully")

            return ContainerResult(
                exit_code=0,
                stdout=stdout,
                stderr=stderr,
                container_id=None,  # Auto-removed
                success=True,
            )

        except ContainerError as e:
            logger.exception("Container execution failed")
            return ContainerResult(
                exit_code=e.exit_status,
                stdout=e.stdout.decode("utf-8") if e.stdout else "",
                stderr=e.stderr.decode("utf-8") if e.stderr else str(e),
                success=False,
            )
        except DockerException as e:
            logger.exception("Docker error")
            return ContainerResult(exit_code=-1, stderr=str(e), success=False)
        except Exception as e:
            logger.exception("Unexpected error")
            return ContainerResult(exit_code=-1, stderr=str(e), success=False)

    def run_container_async(self, container_spec: ContainerSpec, volumes: list[Volume], **kwargs: str):  # type: ignore[no-untyped-def]
        """
        Run container in detached mode.

        Args:
            container_spec: Container specification
            volumes: Volume specifications
            **kwargs: Additional docker run options

        Returns:
            Docker Container object for monitoring
        """
        # Convert volumes
        docker_volumes = self._convert_volumes(volumes, container_spec.volume_mounts)

        # Build run arguments for detached mode
        run_kwargs = {
            "image": container_spec.image,
            "command": self._build_command(container_spec),
            "environment": container_spec.env_vars,
            "volumes": docker_volumes,
            "working_dir": container_spec.working_dir,
            "detach": True,  # Run in background
            "labels": container_spec.labels,
            **kwargs,
        }

        # Add security context
        if container_spec.security_context:
            self._apply_security_context(run_kwargs, container_spec.security_context)

        logger.info(f"Starting container in background: {container_spec.name}")
        container = self.client.containers.run(**run_kwargs)

        return container

    def wait_for_container(self, container) -> ContainerResult:  # type: ignore[no-untyped-def]
        """
        Wait for container completion and return results.

        Args:
            container: Docker Container object

        Returns:
            ContainerResult with execution details
        """
        try:
            # Wait for completion
            result = container.wait()
            exit_code = result["StatusCode"]

            # Get logs
            logs = container.logs(stdout=True, stderr=True)
            output = logs.decode("utf-8") if isinstance(logs, bytes) else str(logs)

            # Remove container
            container.remove()

            logger.info(f"Container completed with exit code: {exit_code}")

            return ContainerResult(
                exit_code=exit_code, stdout=output, container_id=container.id, success=(exit_code == 0)
            )

        except DockerException as e:
            logger.exception("Error waiting for container")
            return ContainerResult(exit_code=-1, stderr=str(e), success=False)

    def _convert_volumes(self, volumes: list[Volume], mounts: list) -> dict[str, dict[str, str]]:
        """Convert Volume specs to Docker SDK volume format."""
        docker_volumes = {}

        # Create mapping of volume names to volumes
        volume_map = {vol.name: vol for vol in volumes}

        for mount in mounts:
            if mount.name in volume_map:
                volume = volume_map[mount.name]

                if volume.volume_type == "hostPath":
                    host_path = volume.source.get("path", "")
                    docker_volumes[host_path] = {"bind": mount.mount_path, "mode": "ro" if mount.read_only else "rw"}
                # Add other volume types as needed (tmpfs, etc.)

        return docker_volumes

    def _build_command(self, container_spec: ContainerSpec) -> list[str]:
        """Build command list from container spec."""
        command = []

        if container_spec.command:
            command.extend(container_spec.command)
        if container_spec.args:
            command.extend(container_spec.args)

        return command or []

    def _apply_security_context(self, run_kwargs: dict, security_context: dict) -> None:
        """Apply security context to docker run arguments."""
        if "runAsUser" in security_context:
            run_kwargs["user"] = security_context["runAsUser"]
        if security_context.get("privileged"):
            run_kwargs["privileged"] = True

    def close(self) -> None:
        """Close Docker client connection."""
        if hasattr(self, "client"):
            self.client.close()

    def __enter__(self):  # type: ignore[no-untyped-def]
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Context manager exit."""
        self.close()
