"""
Path Converter

Converts paths between host filesystem and container execution environments.
Builds on existing PathFinder utility to provide consistent mounting strategies
across local, VM, and Kubernetes execution methods.
"""

from pathlib import PurePosixPath
from typing import Union

from upath import UPath

from fluidize.core.types.execution_models import ExecutionContext, ExecutionMode
from fluidize.core.types.runs import ContainerPaths
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class PathConverter:
    """
    Converts paths between host and container environments.

    Uses existing PathFinder utility for host path resolution, then converts
    to appropriate container mount strategies:
    - Local: Clean node-specific mounts (/mnt/{node_id})
    - Cloud: Bucket-wide mounts with full GCS structure
    """

    @staticmethod
    def build_container_paths(context: ExecutionContext) -> ContainerPaths:
        """
        Build container-specific paths from execution context.

        Uses PathFinder to get host paths, then converts to container paths
        based on execution mode mounting strategy.

        Args:
            context: Execution context with node and project info

        Returns:
            ContainerPaths object with container-accessible paths
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"PathConverter: Building paths with run_number={context.run_number}")

        # Get host paths using existing PathFinder
        host_node_path = PathFinder.get_node_path(context.project, context.node.node_id, context.run_number)
        logger.info(f"PathConverter: host_node_path={host_node_path}")

        # Convert to container paths based on execution mode
        if context.execution_mode == ExecutionMode.LOCAL_DOCKER:
            return PathConverter._build_local_container_paths(context, host_node_path)
        elif context.execution_mode in [ExecutionMode.VM_DOCKER, ExecutionMode.KUBERNETES, ExecutionMode.CLOUD_BATCH]:
            return PathConverter._build_cloud_container_paths(context, host_node_path)
        else:
            # Fallback to local strategy
            return PathConverter._build_local_container_paths(context, host_node_path)

    @staticmethod
    def build_volume_mount_mappings(
        context: ExecutionContext, container_paths: ContainerPaths
    ) -> dict[str, dict[str, str]]:
        """
        Build volume mount mappings for container execution.

        Returns mount specifications that execution clients can use
        to create proper volume mounts.

        Args:
            context: Execution context
            container_paths: Container filesystem paths

        Returns:
            Dictionary mapping volume names to mount specifications
        """
        if context.execution_mode == ExecutionMode.LOCAL_DOCKER:
            return PathConverter._build_local_volume_mounts(context)
        elif context.execution_mode in [ExecutionMode.VM_DOCKER, ExecutionMode.KUBERNETES, ExecutionMode.CLOUD_BATCH]:
            return PathConverter._build_cloud_volume_mounts(context)
        else:
            return PathConverter._build_local_volume_mounts(context)

    @staticmethod
    def convert_gcs_to_container_path(gcs_path: str) -> str:
        """
        Convert GCS path to container mount path.

        Args:
            gcs_path: GCS path like gs://bucket/path/to/file

        Returns:
            Container path like /mnt/bucket/path/to/file
        """
        if gcs_path.startswith("gs://"):
            return f"/mnt/{gcs_path[5:]}"  # Remove gs:// prefix
        return gcs_path

    @staticmethod
    def validate_container_paths(container_paths: ContainerPaths) -> dict[str, list[str]]:
        """
        Validate container paths for correctness and security.

        Args:
            container_paths: Container paths to validate

        Returns:
            Dictionary with 'errors', 'warnings', and 'info' lists
        """
        errors = []
        warnings = []
        info = []

        # Use helper methods to reduce complexity
        required_paths = {
            "node_path": container_paths.node_path,
            "simulation_path": container_paths.simulation_path,
            "output_path": container_paths.output_path,
        }

        errors.extend(PathConverter._validate_required_paths(required_paths))
        warnings.extend(PathConverter._validate_path_safety(required_paths))
        errors.extend(PathConverter._validate_input_path(container_paths.input_path))
        info.extend(PathConverter._collect_path_info(required_paths, container_paths.input_path))

        return {"errors": errors, "warnings": warnings, "info": info}

    @staticmethod
    def _validate_required_paths(required_paths: dict[str, Union[PurePosixPath, None]]) -> list[str]:
        """Validate required paths exist and are absolute."""
        errors = []
        for name, path in required_paths.items():
            if path is None:
                errors.append(f"Missing required path: {name}")
                continue

            path_str = str(path)
            if not path_str.startswith("/"):
                errors.append(f"{name} must be absolute: {path_str}")

            # Security: check for path traversal attempts
            if ".." in path_str:
                errors.append(f"{name} contains path traversal: {path_str}")
        return errors

    @staticmethod
    def _validate_path_safety(required_paths: dict[str, Union[PurePosixPath, None]]) -> list[str]:
        """Validate paths for shell safety."""
        warnings = []
        for name, path in required_paths.items():
            if path is None:
                continue

            path_str = str(path)
            # Warn about spaces (can cause shell issues)
            if " " in path_str:
                warnings.append(f"{name} contains spaces: {path_str}")

            # Warn about shell-unsafe characters
            unsafe_chars = ["$", "`", ";", "&", "|", ">", "<", "*", "?"]
            for char in unsafe_chars:
                if char in path_str:
                    warnings.append(f"{name} contains shell-unsafe character '{char}': {path_str}")
        return warnings

    @staticmethod
    def _validate_input_path(input_path: Union[PurePosixPath, None]) -> list[str]:
        """Validate input path if present."""
        errors = []
        if input_path:
            input_str = str(input_path)
            if not input_str.startswith("/"):
                errors.append(f"input_path must be absolute: {input_str}")
            if ".." in input_str:
                errors.append(f"input_path contains path traversal: {input_str}")
        return errors

    @staticmethod
    def _collect_path_info(
        required_paths: dict[str, Union[PurePosixPath, None]], input_path: Union[PurePosixPath, None]
    ) -> list[str]:
        """Collect informational messages about paths."""
        info = []
        for name, path in required_paths.items():
            if path:
                info.append(f"{name}: {path!s}")

        if input_path:
            info.append(f"input_path: {input_path!s}")
        return info

    @staticmethod
    def _build_local_container_paths(context: ExecutionContext, host_node_path: UPath) -> ContainerPaths:
        """Build container paths for local execution with clean mounting."""
        # Local strategy: mount node directory to /mnt/{node_id}
        container_base = f"/mnt/{context.node.node_id}"

        return ContainerPaths(
            node_path=PurePosixPath(container_base),
            simulation_path=PurePosixPath(f"{container_base}/{context.node.simulation_mount_path}"),
            output_path=PurePosixPath(f"{container_base}/{context.node.source_output_folder}"),
            input_path=PurePosixPath("/mnt/input") if context.dependencies else None,
        )

    @staticmethod
    def _build_cloud_container_paths(context: ExecutionContext, host_node_path: UPath) -> ContainerPaths:
        """Build container paths for cloud execution with bucket mounting."""
        # Cloud strategy: preserve GCS bucket structure
        # host_node_path is like: gs://bucket/uid/projects/project_id/node_id
        # Container sees: /mnt/bucket/uid/projects/project_id/node_id

        host_path_str = str(host_node_path)
        if host_path_str.startswith("gs://"):
            container_node_base = PathConverter.convert_gcs_to_container_path(host_path_str)
        else:
            # Fallback if not GCS path
            container_node_base = f"/mnt/data/{context.node.node_id}"

        # Build input path for dependencies
        input_path = None
        if context.dependencies and context.prev_node:
            prev_node_path = PathFinder.get_node_path(context.project, context.prev_node.node_id, context.run_number)
            prev_path_str = str(prev_node_path)
            if prev_path_str.startswith("gs://"):
                prev_container_base = PathConverter.convert_gcs_to_container_path(prev_path_str)
                input_path = PurePosixPath(f"{prev_container_base}/{context.prev_node.source_output_folder}")

        return ContainerPaths(
            node_path=PurePosixPath(container_node_base),
            simulation_path=PurePosixPath(f"{container_node_base}/{context.node.simulation_mount_path}"),
            output_path=PurePosixPath(f"{container_node_base}/{context.node.source_output_folder}"),
            input_path=input_path,
        )

    @staticmethod
    def _build_local_volume_mounts(context: ExecutionContext) -> dict[str, dict[str, str]]:
        """Build volume mounts for local execution."""
        mounts = {}

        # Main node directory mount
        host_node_path = PathFinder.get_node_path(context.project, context.node.node_id, context.run_number)

        mounts["node-data"] = {
            "host_path": str(host_node_path),
            "container_path": f"/mnt/{context.node.node_id}",
            "type": "hostPath",
        }

        # Input mount if dependencies exist
        if context.dependencies and context.prev_node:
            prev_node_path = PathFinder.get_node_path(context.project, context.prev_node.node_id, context.run_number)
            input_host_path = prev_node_path / context.prev_node.source_output_folder

            mounts["input-data"] = {
                "host_path": str(input_host_path),
                "container_path": "/mnt/input",
                "type": "hostPath",
            }

        return mounts

    @staticmethod
    def _build_cloud_volume_mounts(context: ExecutionContext) -> dict[str, dict[str, str]]:
        """Build volume mounts for cloud execution."""
        mounts = {}

        # Get bucket name from project path
        projects_path = PathFinder.get_projects_path()
        projects_path_str = str(projects_path)

        bucket_name = projects_path_str.split("/")[2] if projects_path_str.startswith("gs://") else "fluidize-users"

        # Main bucket mount via GCS Fuse
        mounts["user-bucket"] = {
            "host_path": f"gs://{bucket_name}",
            "container_path": f"/mnt/{bucket_name}",
            "type": "gcsFuse",
        }

        return mounts
