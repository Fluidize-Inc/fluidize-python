"""
Execution Models for Universal Container Specifications

This package provides enhanced context classes that extend beyond the simple
node + prev_node pattern to support complex dependencies, resource requirements,
and advanced scheduling for all execution methods.
"""

from .container_spec import ContainerSpec, PodSpec, Volume, VolumeMount
from .execution_context import ExecutionContext, create_execution_context
from .execution_hints import ExecutionHints, RetryPolicy
from .execution_mode import ExecutionMode
from .resource_requirements import GPUType, NodePoolType, ResourceRequirements
from .workflow_context import WorkflowContext

__all__ = [
    "ContainerSpec",
    "ExecutionContext",
    "ExecutionHints",
    "ExecutionMode",
    "GPUType",
    "NodePoolType",
    "PodSpec",
    "ResourceRequirements",
    "RetryPolicy",
    "Volume",
    "VolumeMount",
    "WorkflowContext",
    "create_execution_context",
]
