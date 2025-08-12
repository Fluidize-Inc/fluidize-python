"""
Universal Container Builder

Ties together all utility modules to build complete container specifications
from ExecutionContext for any execution method.
"""

from dataclasses import dataclass
from typing import Optional

from fluidize.core.types.execution_models import ContainerSpec, ExecutionContext, ExecutionMode, PodSpec
from fluidize.core.types.runs import ContainerPaths

from .environment_builder import EnvironmentBuilder
from .path_converter import PathConverter
from .resource_builder import ResourceBuilder, ResourceSpec
from .volume_builder import VolumeBuilder, VolumeSpec


@dataclass
class UniversalContainerSpec:
    """Complete specification for container execution across all methods."""

    container_spec: ContainerSpec
    pod_spec: Optional[PodSpec] = None
    volume_spec: Optional[VolumeSpec] = None
    resource_spec: Optional[ResourceSpec] = None
    container_paths: Optional[ContainerPaths] = None
    docker_args: Optional[list[str]] = None


class UniversalContainerBuilder:
    """
    Builds universal container specifications from ExecutionContext.

    This is the main entry point that orchestrates all utility modules
    to create specifications that work across Docker, VM, and Kubernetes.
    """

    @staticmethod
    def build_container_spec(context: ExecutionContext) -> UniversalContainerSpec:
        """
        Build complete container specification from execution context.

        Args:
            context: Execution context with all node and project info

        Returns:
            UniversalContainerSpec with all required specifications
        """
        # Step 1: Build container paths
        container_paths = PathConverter.build_container_paths(context)

        # Step 2: Build environment variables
        env_vars = EnvironmentBuilder.build_complete_env_vars(context, container_paths)

        # Step 3: Build volumes
        volume_spec = VolumeBuilder.build_volume_spec(context)

        # Step 4: Build resources (for Kubernetes)
        resource_spec = None
        if context.execution_mode == ExecutionMode.KUBERNETES:
            resource_spec = ResourceBuilder.build_resource_spec(context)

        # Step 5: Create base container spec
        container_spec = ContainerSpec(
            name=f"fluidize-{context.node.node_id}",
            image=context.node.container_image,
            command=["/bin/bash", f"{container_paths.node_path}/main.sh"],
            env_vars=env_vars,
            volume_mounts=volume_spec.volume_mounts,
            working_dir=str(container_paths.simulation_path),
            labels={
                "fluidize.node_id": context.node.node_id,
                "fluidize.project_id": context.project.id,
                "fluidize.execution_mode": context.execution_mode.value,
            },
        )

        # Step 6: Add resources to container spec if available
        if resource_spec:
            container_spec.resources = ResourceBuilder.build_kubernetes_resources(resource_spec)

        # Step 7: Create pod spec for Kubernetes
        pod_spec = None
        if context.execution_mode == ExecutionMode.KUBERNETES:
            pod_spec = PodSpec(
                containers=[container_spec],
                volumes=volume_spec.volumes,
                restart_policy="Never",
                labels=container_spec.labels.copy(),
                node_selector=resource_spec.node_selector if resource_spec else None,
                tolerations=resource_spec.tolerations if resource_spec else None,
            )

        # Step 8: Build Docker arguments for local/VM execution
        docker_args = None
        if context.execution_mode in [ExecutionMode.LOCAL_DOCKER, ExecutionMode.VM_DOCKER]:
            docker_args = UniversalContainerBuilder._build_docker_args(container_spec, volume_spec, resource_spec)

        return UniversalContainerSpec(
            container_spec=container_spec,
            pod_spec=pod_spec,
            volume_spec=volume_spec,
            resource_spec=resource_spec,
            container_paths=container_paths,
            docker_args=docker_args,
        )

    @staticmethod
    def _build_docker_args(
        container_spec: ContainerSpec, volume_spec: VolumeSpec, resource_spec: Optional[ResourceSpec]
    ) -> list[str]:
        """
        Build complete Docker CLI arguments.

        Args:
            container_spec: Container specification
            volume_spec: Volume specification
            resource_spec: Resource specification (optional)

        Returns:
            List of Docker CLI arguments
        """
        args = ["docker", "run", "--rm"]

        # Platform
        args.extend(["--platform", "linux/amd64"])

        # Volumes
        volume_args = VolumeBuilder.build_docker_volume_args(volume_spec)
        args.extend(volume_args)

        # Environment variables
        for key, value in container_spec.env_vars.items():
            args.extend(["-e", f"{key}={value}"])

        # Working directory
        if container_spec.working_dir:
            args.extend(["--workdir", container_spec.working_dir])

        # Resources (if available)
        if resource_spec:
            resource_args = ResourceBuilder.build_docker_resource_args(resource_spec)
            args.extend(resource_args)

        # Labels
        for key, value in container_spec.labels.items():
            args.extend(["--label", f"{key}={value}"])

        # Entrypoint override
        args.extend(["--entrypoint", "/bin/bash"])

        # Image
        args.append(container_spec.image)

        # Command
        args.extend(container_spec.command)

        return args

    @staticmethod
    def validate_spec(spec: UniversalContainerSpec) -> dict[str, list[str]]:
        """
        Validate the complete specification.

        Args:
            spec: Universal container specification

        Returns:
            Dictionary with 'errors', 'warnings', and 'info' lists
        """
        all_errors = []
        all_warnings = []
        all_info = []

        # Validate paths
        if spec.container_paths:
            path_validation = PathConverter.validate_container_paths(spec.container_paths)
            all_errors.extend(path_validation["errors"])
            all_warnings.extend(path_validation["warnings"])
            all_info.extend(path_validation["info"])

        # Validate environment variables
        env_validation = EnvironmentBuilder.validate_env_vars(spec.container_spec.env_vars)
        all_errors.extend(env_validation["errors"])
        all_warnings.extend(env_validation["warnings"])
        all_info.extend(env_validation["info"])

        # Validate volumes
        if spec.volume_spec:
            volume_validation = VolumeBuilder.validate_volumes(spec.volume_spec)
            all_errors.extend(volume_validation["errors"])
            all_warnings.extend(volume_validation["warnings"])
            all_info.extend(volume_validation["info"])

        # Basic container spec validation
        if not spec.container_spec.image:
            all_errors.append("Container image not specified")

        if not spec.container_spec.command:
            all_errors.append("Container command not specified")

        return {"errors": all_errors, "warnings": all_warnings, "info": all_info}
