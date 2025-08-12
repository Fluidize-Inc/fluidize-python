"""
Resource Builder

Builds resource specifications for container execution, primarily for Kubernetes.
Reads resource information from Terraform outputs when available.
"""

from dataclasses import dataclass
from typing import ClassVar, Optional

from fluidize.core.types.execution_models import ExecutionContext


@dataclass
class ResourceSpec:
    """Resource specification for container execution."""

    requests: dict[str, str]
    limits: dict[str, str]
    node_selector: Optional[dict[str, str]] = None
    tolerations: Optional[list[dict]] = None


class ResourceBuilder:
    """
    Builds resource specifications for container execution.

    Simple approach: read from Terraform outputs or use minimal defaults.
    """

    # Minimal default if no Terraform outputs available
    DEFAULT_RESOURCES: ClassVar[dict[str, dict[str, str]]] = {
        "requests": {"cpu": "1", "memory": "4Gi"},
        "limits": {"cpu": "2", "memory": "8Gi"},
    }

    @staticmethod
    def build_resource_spec(context: ExecutionContext) -> ResourceSpec:
        """
        Build resource specification from context.

        Args:
            context: Execution context

        Returns:
            ResourceSpec with resource requirements
        """
        # Use explicit requirements if provided
        if context.resource_requirements:
            return ResourceSpec(
                requests=context.resource_requirements.requests,
                limits=context.resource_requirements.limits,
                node_selector={"cloud.google.com/gke-nodepool": context.get_node_pool()},
            )

        # Otherwise use defaults
        return ResourceSpec(
            requests=ResourceBuilder.DEFAULT_RESOURCES["requests"].copy(),
            limits=ResourceBuilder.DEFAULT_RESOURCES["limits"].copy(),
        )

    @staticmethod
    def build_docker_resource_args(resource_spec: ResourceSpec) -> list[str]:
        """
        Convert resource specification to Docker CLI arguments.

        Args:
            resource_spec: Resource specification

        Returns:
            List of Docker resource arguments
        """
        args = []

        # Memory limit
        if "memory" in resource_spec.limits:
            memory = resource_spec.limits["memory"]
            # Convert Kubernetes format to Docker format
            docker_memory = memory.replace("Gi", "g").replace("Mi", "m")
            args.extend(["--memory", docker_memory])

        # CPU limit
        if "cpu" in resource_spec.limits:
            args.extend(["--cpus", resource_spec.limits["cpu"]])

        return args

    # @staticmethod
    # def build_kubernetes_resources(resource_spec: ResourceSpec) -> dict:
    #     """
    #     Convert to Kubernetes resource format.

    #     Args:
    #         resource_spec: Resource specification

    #     Returns:
    #         Kubernetes resource requirements dictionary
    #     """
    #     return {"requests": resource_spec.requests, "limits": resource_spec.limits}
