"""
Project-scoped runs manager for user-friendly run operations.
"""

from typing import Any

from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload


class ProjectRuns:
    """
    Runs manager scoped to a specific project.

    Provides convenient run operations without requiring users to pass
    project context repeatedly.
    """

    def __init__(self, backend: Any, project: ProjectSummary) -> None:
        """
        Initialize project-scoped runs manager.

        Args:
            backend: Backend adapter (FluidizeSDK or LocalBackend)
            project: The project this runs manager is bound to
        """
        self.backend = backend
        self.project = project

    def run_flow(self, payload: RunFlowPayload) -> dict[str, Any]:
        """
        Execute a flow run for this project.

        Args:
            payload: Run configuration (name, description, tags)

        Returns:
            Dictionary with flow_status and run_number
        """
        return self.backend.runs.run_flow(self.project, payload)  # type: ignore[no-any-return]

    def list(self) -> list[str]:
        """
        List all runs for this project.

        Returns:
            List of run identifiers for this project
        """
        return self.backend.runs.list_runs(self.project)  # type: ignore[no-any-return]

    def get_status(self, run_number: int) -> dict[str, Any]:
        """
        Get the status of a specific run for this project.

        Args:
            run_number: The run number to check

        Returns:
            Dictionary with run status information
        """
        return self.backend.runs.get_run_status(self.project, run_number)  # type: ignore[no-any-return]
