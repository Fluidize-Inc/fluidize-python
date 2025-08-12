"""
Enhanced execution context that extends beyond node + prev_node pattern.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary

from .execution_hints import ExecutionHints
from .execution_mode import ExecutionMode
from .resource_requirements import NodePoolType, ResourceRequirements
from .workflow_context import WorkflowContext


@dataclass
class ExecutionContext:
    """
    Enhanced execution context that extends beyond node + prev_node pattern.

    This context provides all information needed to build universal container
    specifications that work across all execution methods.
    """

    # Core node information (maintains backwards compatibility)
    node: nodeProperties_simulation
    project: ProjectSummary
    prev_node: Optional[nodeProperties_simulation] = None

    # Enhanced dependency management
    dependencies: list[str] = field(default_factory=list)  # Multiple input nodes
    dependency_nodes: list[nodeProperties_simulation] = field(default_factory=list)

    # Resource and execution requirements
    resource_requirements: Optional[ResourceRequirements] = None
    execution_hints: Optional[ExecutionHints] = None

    # Workflow context for DAG execution
    workflow_context: Optional[WorkflowContext] = None

    # Execution mode
    execution_mode: ExecutionMode = ExecutionMode.LOCAL_DOCKER

    # Additional context
    run_id: Optional[str] = None
    run_number: Optional[int] = None
    custom_env_vars: dict[str, str] = field(default_factory=dict)
    custom_labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize derived fields and validate context."""

        # Auto-populate dependencies from prev_node for backwards compatibility
        if self.prev_node and not self.dependencies:
            self.dependencies = [str(self.prev_node.node_id)]
            self.dependency_nodes = [self.prev_node]

        # Set default resource requirements if not provided
        if self.resource_requirements is None:
            self.resource_requirements = self._detect_resource_requirements()

        # Set default execution hints if not provided
        if self.execution_hints is None:
            self.execution_hints = ExecutionHints()

    def _detect_resource_requirements(self) -> ResourceRequirements:
        """Auto-detect resource requirements from node properties."""

        # Start with defaults
        requirements = ResourceRequirements()

        # Analyze container image for hints
        image = self.node.container_image.lower()

        # GPU detection
        if any(gpu_hint in image for gpu_hint in ["gpu", "cuda", "tensorflow-gpu", "pytorch-gpu"]):
            requirements.gpu_count = 1
            requirements.node_pool_preference = NodePoolType.GPU
            requirements.memory_limit = "8Gi"  # GPU workloads need more memory

        # High CPU detection for CFD/simulation workloads
        elif any(cpu_hint in image for cpu_hint in ["openfoam", "ansys", "comsol", "cfd"]):
            requirements.cpu_limit = "4000m"  # 4 CPUs for CFD
            requirements.memory_limit = "8Gi"
            requirements.node_pool_preference = NodePoolType.MEDIUM_CPU

        # ML/Data science detection
        elif any(ml_hint in image for ml_hint in ["jupyter", "tensorflow", "pytorch", "sklearn"]):
            requirements.cpu_limit = "2000m"
            requirements.memory_limit = "4Gi"
            requirements.node_pool_preference = NodePoolType.SMALL_CPU

        return requirements

    def has_dependencies(self) -> bool:
        """Check if this node has input dependencies."""
        return len(self.dependencies) > 0

    def requires_gpu(self) -> bool:
        """Check if GPU resources are required."""
        return self.resource_requirements.requires_gpu() if self.resource_requirements else False

    def get_node_pool(self) -> str:
        """Get the appropriate Kubernetes node pool."""
        return self.resource_requirements.get_node_pool() if self.resource_requirements else "small-cpu-pool"

    def is_workflow_execution(self) -> bool:
        """Check if this is part of a workflow execution."""
        return self.workflow_context is not None

    def get_execution_labels(self) -> dict[str, str]:
        """Get all labels for this execution context."""
        labels = {
            "app": "fluidize",
            "node-id": str(self.node.node_id),
            "project-id": str(self.project.id),
            "execution-mode": str(self.execution_mode.value),
        }

        # Add workflow labels if available
        if self.workflow_context:
            labels.update({
                "workflow-id": self.workflow_context.workflow_id,
                "workflow-name": self.workflow_context.workflow_name,
                "step-name": self.workflow_context.step_name,
            })
            labels.update(self.workflow_context.workflow_labels)

        # Add custom labels
        labels.update(self.custom_labels)

        return labels

    def get_standard_env_vars(self) -> dict[str, str]:
        """Get standard Fluidize environment variables."""
        env_vars = {
            "FLUIDIZE_NODE_ID": str(self.node.node_id),
            "FLUIDIZE_PROJECT_ID": str(self.project.id),
            "FLUIDIZE_EXECUTION_MODE": str(self.execution_mode.value),
        }

        # Add run context if available
        if self.run_id:
            env_vars["FLUIDIZE_RUN_ID"] = self.run_id
        if self.run_number:
            env_vars["FLUIDIZE_RUN_NUMBER"] = str(self.run_number)

        # Add workflow context if available
        if self.workflow_context:
            env_vars.update({
                "FLUIDIZE_WORKFLOW_ID": self.workflow_context.workflow_id,
                "FLUIDIZE_STEP_NAME": self.workflow_context.step_name,
            })

        # Add custom environment variables
        env_vars.update(self.custom_env_vars)

        return env_vars


def create_execution_context(
    node: nodeProperties_simulation,
    project: ProjectSummary,
    prev_node: Optional[nodeProperties_simulation] = None,
    **kwargs: Any,
) -> ExecutionContext:
    """
    Factory function to create ExecutionContext with backwards compatibility.

    This function maintains the existing node + prev_node interface while
    allowing for enhanced context creation.
    """
    return ExecutionContext(node=node, project=project, prev_node=prev_node, **kwargs)
