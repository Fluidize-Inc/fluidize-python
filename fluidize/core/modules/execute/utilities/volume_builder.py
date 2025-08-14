"""
Volume Builder

Builds volume specifications for container execution across different environments.
Handles volume creation for local bind mounts, GCS Fuse mounts, and Kubernetes volumes.
"""

from dataclasses import dataclass
from typing import Optional

from fluidize.core.types.execution_models import ExecutionContext, ExecutionMode, Volume, VolumeMount
from fluidize.core.utils.pathfinder.path_finder import PathFinder


@dataclass
class VolumeSpec:
    """Complete volume specification for container execution."""

    volumes: list[Volume]
    volume_mounts: list[VolumeMount]


class VolumeBuilder:
    """
    Builds volume specifications for container execution.

    Creates appropriate volume types and mount configurations
    based on execution mode:
    - Local: Multiple specific directory mounts (node, input, output)
    - Cloud: Single GCS Fuse bucket mount (input/output via env vars only)
    """

    @staticmethod
    def build_volume_spec(context: ExecutionContext) -> VolumeSpec:
        """
        Build complete volume specification for execution context.

        Args:
            context: Execution context with node and project info

        Returns:
            VolumeSpec with volumes and volume mounts
        """
        if context.execution_mode == ExecutionMode.LOCAL_DOCKER:
            return VolumeBuilder._build_local_volume_spec(context)
        elif context.execution_mode in [ExecutionMode.VM_DOCKER, ExecutionMode.KUBERNETES, ExecutionMode.CLOUD_BATCH]:
            return VolumeBuilder._build_cloud_volume_spec(context)
        else:
            # Fallback to local strategy
            return VolumeBuilder._build_local_volume_spec(context)

    @staticmethod
    def _build_local_volume_spec(context: ExecutionContext) -> VolumeSpec:
        """
        Build volume spec for local execution with multiple specific mounts.

        Local strategy creates separate volumes for:
        - Node directory
        - Input directory (if dependencies exist)
        - Output directory
        """
        volumes = []
        volume_mounts = []

        # Get host paths
        node_paths = VolumeBuilder._get_node_paths(context)

        # Node volume - main working directory
        node_volume = Volume(name="node-data", volume_type="hostPath", source={"path": str(node_paths["node_path"])})
        volumes.append(node_volume)

        node_mount = VolumeMount(name="node-data", mount_path=f"/mnt/{context.node.node_id}", read_only=False)
        volume_mounts.append(node_mount)

        # Input volume - if there are dependencies
        if context.dependencies and context.prev_node and node_paths.get("input_path"):
            input_volume = Volume(
                name="input-data", volume_type="hostPath", source={"path": str(node_paths["input_path"])}
            )
            volumes.append(input_volume)

            input_mount = VolumeMount(
                name="input-data",
                mount_path="/mnt/input",
                read_only=True,  # Input should be read-only
            )
            volume_mounts.append(input_mount)

        # Output volume - separate mount for output directory
        if node_paths.get("output_path"):
            output_volume = Volume(
                name="output-data", volume_type="hostPath", source={"path": str(node_paths["output_path"])}
            )
            volumes.append(output_volume)

            # Output path in container follows pattern from local Execute.py
            output_mount = VolumeMount(
                name="output-data",
                mount_path=f"/mnt/{context.node.node_id}/{context.node.source_output_folder}",
                read_only=False,
            )
            volume_mounts.append(output_mount)

        return VolumeSpec(volumes=volumes, volume_mounts=volume_mounts)

    @staticmethod
    def _build_cloud_volume_spec(context: ExecutionContext) -> VolumeSpec:
        """
        Build volume spec for cloud execution with single GCS Fuse mount.

        Cloud strategy creates only one volume:
        - Entire GCS bucket mount
        Input/output paths are accessed within this mount via environment variables
        """
        volumes = []
        volume_mounts = []

        # Get bucket name from project path
        projects_path = PathFinder.get_projects_path()
        projects_path_str = str(projects_path)

        bucket_name = projects_path_str.split("/")[2] if projects_path_str.startswith("gs://") else "fluidize_users"

        # Single GCS Fuse volume for entire bucket
        bucket_volume = Volume(name="user-bucket", volume_type="gcsFuse", source={"bucket": f"gs://{bucket_name}"})
        volumes.append(bucket_volume)

        # Mount entire bucket - exactly like vm_job_builder.py line 150
        bucket_mount = VolumeMount(name="user-bucket", mount_path=f"/mnt/{bucket_name}", read_only=False)
        volume_mounts.append(bucket_mount)

        # NO separate input/output mounts for cloud - handled via env vars

        return VolumeSpec(volumes=volumes, volume_mounts=volume_mounts)

    @staticmethod
    def build_docker_volume_args(volume_spec: VolumeSpec) -> list[str]:
        """
        Convert volume specification to Docker CLI volume arguments.

        Args:
            volume_spec: Volume specification

        Returns:
            List of Docker volume arguments (-v host:container)
        """
        volume_args = []

        # Create mapping of volume names to volumes
        volume_map = {vol.name: vol for vol in volume_spec.volumes}

        for mount in volume_spec.volume_mounts:
            if mount.name in volume_map:
                volume = volume_map[mount.name]

                if volume.volume_type == "hostPath":
                    host_path = volume.source["path"]
                    mount_arg = f"{host_path}:{mount.mount_path}"
                    if mount.read_only:
                        mount_arg += ":ro"
                    volume_args.extend(["-v", mount_arg])

                elif volume.volume_type == "gcsFuse":
                    # For Docker on VM, GCS Fuse is already mounted on host
                    # We bind the host FUSE mount into container
                    bucket_name = volume.source["bucket"]
                    if bucket_name.startswith("gs://"):
                        bucket_name = bucket_name[5:]  # Remove gs://

                    # The FUSE mount is at /mnt/{bucket_name} on the VM
                    mount_arg = f"/mnt/{bucket_name}:{mount.mount_path}"
                    if mount.read_only:
                        mount_arg += ":ro"
                    volume_args.extend(["-v", mount_arg])

        return volume_args

    @staticmethod
    def build_kubernetes_volumes(volume_spec: VolumeSpec) -> list[dict]:
        """
        Convert volume specification to Kubernetes volume objects.

        Args:
            volume_spec: Volume specification

        Returns:
            List of Kubernetes volume dictionaries
        """
        k8s_volumes = []

        for volume in volume_spec.volumes:
            if volume.volume_type == "hostPath":
                k8s_volume = {
                    "name": volume.name,
                    "hostPath": {"path": volume.source["path"], "type": volume.source.get("type", "Directory")},
                }
                k8s_volumes.append(k8s_volume)

            elif volume.volume_type == "gcsFuse":
                # For GCS Fuse in Kubernetes, we use CSI driver
                bucket_name = volume.source["bucket"]
                if bucket_name.startswith("gs://"):
                    bucket_name = bucket_name[5:]  # Remove gs://

                k8s_volume = {
                    "name": volume.name,
                    "csi": {
                        "driver": "gcsfuse.csi.storage.gke.io",
                        "volumeAttributes": {"bucketName": bucket_name, "mountOptions": "implicit-dirs"},
                    },
                }
                k8s_volumes.append(k8s_volume)

        return k8s_volumes

    @staticmethod
    def build_kubernetes_volume_mounts(volume_spec: VolumeSpec) -> list[dict]:
        """
        Convert volume mounts to Kubernetes volume mount objects.

        Args:
            volume_spec: Volume specification

        Returns:
            List of Kubernetes volume mount dictionaries
        """
        k8s_mounts = []

        for mount in volume_spec.volume_mounts:
            k8s_mount = {"name": mount.name, "mountPath": mount.mount_path, "readOnly": mount.read_only}

            if mount.sub_path:
                k8s_mount["subPath"] = mount.sub_path

            k8s_mounts.append(k8s_mount)

        return k8s_mounts

    @staticmethod
    def validate_volumes(volume_spec: VolumeSpec) -> dict[str, list[str]]:
        """
        Validate volume specification for correctness and compatibility.

        Args:
            volume_spec: Volume specification to validate

        Returns:
            Dictionary with 'errors', 'warnings', and 'info' lists
        """
        errors = []
        warnings = []
        info = []

        # Check volume/mount consistency
        volume_names = {vol.name for vol in volume_spec.volumes}
        mount_names = {mount.name for mount in volume_spec.volume_mounts}

        # Check for orphaned mounts
        orphaned_mounts = mount_names - volume_names
        if orphaned_mounts:
            errors.extend([f"Volume mount references non-existent volume: {name}" for name in orphaned_mounts])

        # Check for unused volumes
        unused_volumes = volume_names - mount_names
        if unused_volumes:
            warnings.extend([f"Volume defined but not mounted: {name}" for name in unused_volumes])

        # Validate individual volumes
        for volume in volume_spec.volumes:
            volume_errors, volume_warnings = VolumeBuilder._validate_volume(volume)
            errors.extend(volume_errors)
            warnings.extend(volume_warnings)

        # Validate individual mounts
        for mount in volume_spec.volume_mounts:
            mount_errors, mount_warnings = VolumeBuilder._validate_mount(mount)
            errors.extend(mount_errors)
            warnings.extend(mount_warnings)

        # Info messages
        info.append(f"Total volumes: {len(volume_spec.volumes)}")
        info.append(f"Total volume mounts: {len(volume_spec.volume_mounts)}")

        volume_types = [vol.volume_type for vol in volume_spec.volumes]
        for vol_type in set(volume_types):
            count = volume_types.count(vol_type)
            info.append(f"{vol_type} volumes: {count}")

        return {"errors": errors, "warnings": warnings, "info": info}

    @staticmethod
    def _get_node_paths(context: ExecutionContext) -> dict[str, Optional[str]]:
        """Get host paths for node execution."""
        paths: dict[str, Optional[str]] = {}

        # Node path - use the node's actual directory (already run-specific)
        paths["node_path"] = str(context.node.directory)

        # Output path - use node's directory parent for run-specific outputs
        paths["output_path"] = str(context.node.directory.parent / "outputs" / str(context.node.node_id))

        # Input path - if there are dependencies
        if context.dependencies and context.prev_node:
            # Previous node's directory is also already run-specific
            paths["input_path"] = str(context.prev_node.directory.parent / "outputs" / str(context.prev_node.node_id))
        else:
            paths["input_path"] = None

        return paths

    @staticmethod
    def _validate_volume(volume: Volume) -> tuple[list[str], list[str]]:
        """Validate individual volume configuration."""
        errors = []
        warnings = []

        # Basic validation
        errors.extend(VolumeBuilder._validate_volume_basics(volume))

        # Type-specific validation
        if volume.volume_type == "hostPath":
            volume_errors, volume_warnings = VolumeBuilder._validate_hostpath_volume(volume)
            errors.extend(volume_errors)
            warnings.extend(volume_warnings)
        elif volume.volume_type == "gcsFuse":
            volume_errors, volume_warnings = VolumeBuilder._validate_gcsfuse_volume(volume)
            errors.extend(volume_errors)
            warnings.extend(volume_warnings)

        return errors, warnings

    @staticmethod
    def _validate_volume_basics(volume: Volume) -> list[str]:
        """Validate basic volume properties."""
        errors = []
        if not volume.name:
            errors.append("Volume missing name")
        if not volume.volume_type:
            errors.append(f"Volume {volume.name} missing type")
        return errors

    @staticmethod
    def _validate_hostpath_volume(volume: Volume) -> tuple[list[str], list[str]]:
        """Validate hostPath volume configuration."""
        errors = []
        warnings = []

        if "path" not in volume.source:
            errors.append(f"hostPath volume {volume.name} missing path")
        elif not volume.source["path"]:
            errors.append(f"hostPath volume {volume.name} has empty path")
        elif not volume.source["path"].startswith("/"):
            warnings.append(f"hostPath volume {volume.name} path should be absolute: {volume.source['path']}")

        return errors, warnings

    @staticmethod
    def _validate_gcsfuse_volume(volume: Volume) -> tuple[list[str], list[str]]:
        """Validate gcsFuse volume configuration."""
        errors = []
        warnings = []

        if "bucket" not in volume.source:
            errors.append(f"gcsFuse volume {volume.name} missing bucket")
        elif not volume.source["bucket"]:
            errors.append(f"gcsFuse volume {volume.name} has empty bucket")
        elif not volume.source["bucket"].startswith("gs://"):
            warnings.append(f"gcsFuse volume {volume.name} bucket should start with gs://")

        return errors, warnings

    @staticmethod
    def _validate_mount(mount: VolumeMount) -> tuple[list[str], list[str]]:
        """Validate individual volume mount configuration."""
        errors = []
        warnings: list[str] = []

        if not mount.name:
            errors.append("Volume mount missing name")

        if not mount.mount_path:
            errors.append(f"Volume mount {mount.name} missing mount_path")
        elif not mount.mount_path.startswith("/"):
            errors.append(f"Volume mount {mount.name} mount_path must be absolute: {mount.mount_path}")

        # Security checks
        if mount.mount_path and ".." in mount.mount_path:
            errors.append(f"Volume mount {mount.name} contains path traversal: {mount.mount_path}")

        if mount.sub_path and ".." in mount.sub_path:
            errors.append(f"Volume mount {mount.name} subPath contains path traversal: {mount.sub_path}")

        return errors, warnings
