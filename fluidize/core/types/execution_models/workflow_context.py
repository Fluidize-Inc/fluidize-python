"""
Workflow context for DAG-based execution.
"""

from dataclasses import dataclass, field
from typing import Optional

from .execution_hints import RetryPolicy


@dataclass
class WorkflowContext:
    """Context information for workflow execution."""

    # Workflow identification
    workflow_id: str
    workflow_name: str
    step_name: str

    # Parallel execution
    parallel_group: Optional[str] = None
    execution_order: int = 0

    # Dependencies and flow
    depends_on: list[str] = field(default_factory=list)

    # Retry and error handling
    retry_policy: Optional[RetryPolicy] = None
    continue_on_failure: bool = False

    # Workflow metadata
    workflow_labels: dict[str, str] = field(default_factory=dict)
    workflow_annotations: dict[str, str] = field(default_factory=dict)
