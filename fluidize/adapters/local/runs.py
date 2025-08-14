"""
Local runs handler - implements run_flow functionality for local adapter.
"""

import asyncio
from typing import Any

import networkx as nx
from upath import UPath

from fluidize.core.constants import FileConstants
from fluidize.core.modules.graph.process import ProcessGraph
from fluidize.core.modules.run.project.project_runner import ProjectRunner
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload
from fluidize.core.utils.dataloader.data_loader import DataLoader
from fluidize.core.utils.pathfinder.path_finder import PathFinder


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
        graph: nx.DiGraph = nx.DiGraph()

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

    def list_node_outputs(self, project: ProjectSummary, run_number: int, node_id: str) -> list[str]:
        """
        List all output files for a specific node in a run, including files in subdirectories (1 level deep).

        Args:
            project: The project containing the run
            run_number: The run number
            node_id: The node ID to list outputs for

        Returns:
            List of relative file paths within the node's output directory (including subdirectories)
        """
        output_path = PathFinder.get_node_output_path(project, run_number, node_id)

        if not DataLoader.check_file_exists(output_path) and not output_path.exists():
            return []

        all_files = []

        # Get files in the root output directory
        files = DataLoader.list_files(output_path)
        all_files.extend([file.name for file in files])

        # Get files in subdirectories (1 level deep)
        subdirs = DataLoader.list_directories(output_path)
        for subdir in subdirs:
            subdir_files = DataLoader.list_files(subdir)
            # Include the subdirectory name in the relative path
            all_files.extend([f"{subdir.name}/{file.name}" for file in subdir_files])

        return all_files

    def get_output_path(self, project: ProjectSummary, run_number: int, node_id: str) -> UPath:
        """
        Get the full path to a node's output directory.

        Args:
            project: The project containing the run
            run_number: The run number
            node_id: The node ID

        Returns:
            UPath to the node's output directory
        """
        return PathFinder.get_node_output_path(project, run_number, node_id)
