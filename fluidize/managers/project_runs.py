"""
Project-scoped runs manager for user-friendly run operations.
"""

from typing import Any

from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload


class ProjectRuns:
    """
    Runs manager for a specific project.

    Provides run operations like executing workflows without requiring
    project context on each method call.
    """

    def __init__(self, adapter: Any, project: ProjectSummary) -> None:
        """
        Initialize project-scoped runs manager.

        Args:
            adapter: adapter adapter (FluidizeSDK or Localadapter)
            project: The project this runs manager is bound to
        """
        self.adapter = adapter
        self.project = project

    def run_flow(self, payload: RunFlowPayload) -> dict[str, Any]:
        """
        Execute a flow run for this project.

        Args:
            payload: Run configuration (name, description, tags)

        Returns:
            Dictionary with flow_status and run_number
        """
        return self.adapter.runs.run_flow(self.project, payload)  # type: ignore[no-any-return]

    def list(self) -> list[str]:
        """
        List all runs for this project.

        Returns:
            List of run identifiers for this project
        """
        return self.adapter.runs.list_runs(self.project)  # type: ignore[no-any-return]

    def get_status(self, run_number: int) -> dict[str, Any]:
        """
        Get the status of a specific run for this project.

        Args:
            run_number: The run number to check

        Returns:
            Dictionary with run status information
        """
        return self.adapter.runs.get_run_status(self.project, run_number)  # type: ignore[no-any-return]
