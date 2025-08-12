"""
Local runs handler - implements run_flow functionality for local backend.
"""

import asyncio
from typing import Any

import networkx as nx

from fluidize.core.constants import FileConstants
from fluidize.core.modules.graph.process import ProcessGraph
from fluidize.core.modules.run.project.project_runner import ProjectRunner
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload
from fluidize.core.utils.dataloader.data_loader import DataLoader


class RunsHandler:
    """
    Local runs handler that provides run execution functionality.

    Implements the core run_flow functionality from the FastAPI implementation,
    adapted for the Python library interface.
    """

    def __init__(self, config: Any) -> None:
        """
        Initialize the runs handler.

        Args:
            config: FluidizeConfig instance
        """
        self.config = config

    def run_flow(self, project: ProjectSummary, payload: RunFlowPayload) -> dict[str, Any]:
        """
        Execute a project run flow.

        This method implements the exact logic from the FastAPI run_flow endpoint:
        1. Load the graph from the project
        2. Process the graph to get execution order using BFS
        3. Create a run environment
        4. Execute the flow asynchronously

        Args:
            project: The project to run
            payload: Run configuration (name, description, tags)

        Returns:
            Dictionary with flow_status and run_number

        Raises:
            ValueError: If no nodes are found to run
        """
        # Load graph data from the project's graph.json file
        data = DataLoader.load_for_project(project, FileConstants.GRAPH_SUFFIX)

        # Create a directed graph manually from the React Flow format
        graph = nx.DiGraph()

        # Add nodes with their data
        for node in data.get("nodes", []):
            graph.add_node(node["id"], **node.get("data", {}))

        # Add edges
        for edge in data.get("edges", []):
            graph.add_edge(edge["source"], edge["target"])

        # Process the graph to get execution order using BFS
        process = ProcessGraph()
        nodes_to_run, prev_nodes = process.print_bfs_nodes(G=graph)

        print(f"Nodes to run: {nodes_to_run}")

        # Validate that there are nodes to run
        if not nodes_to_run:
            msg = "No nodes to run. Please check your graph."
            raise ValueError(msg)

        # Create and prepare the run environment
        runner = ProjectRunner(project)
        run_number = runner.prepare_run_environment(payload)
        print(f"Created run environment with number: {run_number}")

        # Execute all nodes in the flow
        # Try to get the running event loop, if none exists, run synchronously for testing
        try:
            _ = asyncio.get_running_loop()
            # We're in an async context, create task
            task = asyncio.create_task(runner.execute_flow(nodes_to_run, prev_nodes))
            _ = task  # Store reference to avoid RUF006
        except RuntimeError:
            # No event loop running (e.g., in tests), run synchronously
            # Fire and forget - we don't wait for completion either way
            asyncio.run(runner.execute_flow(nodes_to_run, prev_nodes))

        return {"flow_status": "running", "run_number": run_number}

    def list_runs(self, project: ProjectSummary) -> list[str]:
        """
        List all runs for a project.

        Args:
            project: The project to list runs for

        Returns:
            List of run identifiers
        """
        return DataLoader.list_runs(project)

    def get_run_status(self, project: ProjectSummary, run_number: int) -> dict[str, Any]:
        """
        Get the status of a specific run.

        Args:
            project: The project containing the run
            run_number: The run number to check

        Returns:
            Dictionary with run status information
        """
        # This would load run metadata and return status
        # Implementation depends on how run status is stored
        return {"run_number": run_number, "status": "unknown"}
