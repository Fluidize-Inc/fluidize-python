"""
Project-scoped runs manager for user-friendly run operations.
"""

from typing import Any

from upath import UPath

from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload


class RunsManager:
    """
    Runs manager for a specific project.

    Provides run operations like executing workflows without requiring
    project context on each method call.
    """

    def __init__(self, adapter: Any, project: ProjectSummary) -> None:
        """
        Args:
            adapter: adapter (FluidizeSDK or LocalAdapter)
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
        return self.adapter.runs.run_flow(project=self.project, payload=payload)  # type: ignore[no-any-return]

    def list_runs(self) -> list[str]:
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

    def list_node_outputs(self, run_number: int, node_id: str) -> list[str]:
        """
        List all output files for a specific node in a run for this project.

        Args:
            run_number: The run number
            node_id: The node ID to list outputs for

        Returns:
            List of relative file paths within the node's output directory
        """
        return self.adapter.runs.list_node_outputs(self.project, run_number, node_id)  # type: ignore[no-any-return]

    def get_output_path(self, run_number: int, node_id: str) -> UPath:
        """
        Get the full path to a node's output directory for this project.

        Args:
            run_number: The run number
            node_id: The node ID

        Returns:
            UPath to the node's output directory
        """
        return self.adapter.runs.get_output_path(self.project, run_number, node_id)  # type: ignore[no-any-return]
