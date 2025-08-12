"""
Top-level runs manager for cross-project run operations.
"""

from typing import Any

from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload


class Runs:
    """Manager for run-related operations across projects."""

    def __init__(self, backend: Any) -> None:
        """
        Initialize the Runs manager.

        Args:
            backend: Backend adapter (FluidizeSDK or LocalBackend)
        """
        self.backend = backend

    def run_flow(self, project: ProjectSummary, payload: RunFlowPayload) -> dict[str, Any]:
        """
        Execute a flow run for the specified project.

        Args:
            project: The project to run
            payload: Run configuration (name, description, tags)

        Returns:
            Dictionary with flow_status and run_number
        """
        return self.backend.runs.run_flow(project, payload)  # type: ignore[no-any-return]

    def list_runs(self, project: ProjectSummary) -> list[str]:
        """
        List all runs for the specified project.

        Args:
            project: The project to list runs for

        Returns:
            List of run identifiers for the project
        """
        return self.backend.runs.list_runs(project)  # type: ignore[no-any-return]

    def get_run_status(self, project: ProjectSummary, run_number: int) -> dict[str, Any]:
        """
        Get the status of a specific run.

        Args:
            project: The project containing the run
            run_number: The run number to check

        Returns:
            Dictionary with run status information
        """
        return self.backend.runs.get_run_status(project, run_number)  # type: ignore[no-any-return]
