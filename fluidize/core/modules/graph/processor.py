"""
Local filesystem-based graph processor.

This module provides the core business logic for graph operations using
the local filesystem, without any cloud or Firebase dependencies.
"""

import contextlib
import shutil
import subprocess
from typing import Optional
from urllib.parse import urlparse

from upath import UPath

from fluidize.core.constants import FileConstants
from fluidize.core.modules.graph.model import Graph
from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
from fluidize.core.types.node import nodeMetadata_simulation, nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.dataloader.data_loader import DataLoader
from fluidize.core.utils.dataloader.data_writer import DataWriter
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class GraphProcessor:
    """
    Local filesystem-based graph processor.

    Handles all graph operations using the filesystem as the source of truth,
    compatible with the FastAPI interface but without cloud dependencies.
    """

    def __init__(self, project: ProjectSummary) -> None:
        """
        Initialize the graph processor.

        Args:
            project: The project to operate on
        """
        self.project = project

    def get_graph(self) -> GraphData:
        """
        Gets the entire graph for the project from graph.json file.

        Returns:
            GraphData containing all nodes and edges
        """
        try:
            project_path = PathFinder.get_project_path(self.project)
            graph_file_path = project_path / FileConstants.GRAPH_SUFFIX

            # Use the Graph model to load and validate the graph
            graph = Graph.from_file(graph_file_path)
            graph.heal()  # Remove any orphaned edges

            return graph.to_graph_data()
        except Exception as e:
            print(f"Error loading graph for project {self.project.id}: {e!s}")
            return GraphData(nodes=[], edges=[])

    def insert_node(self, node: GraphNode, sim_global: bool = True) -> GraphNode:
        """
        Inserts a node from the list of simulations or creates a new one.

        Args:
            node: The node to insert
            sim_global: Whether to use global simulations

        Returns:
            The inserted node
        """
        # Load existing graph
        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX
        graph = Graph.from_file(graph_file_path)

        # Add node to graph
        graph.add_node(node)

        # Save updated graph
        graph.save_to_file(graph_file_path)

        # Create node directory with appropriate content
        node_path = PathFinder.get_node_path(self.project, node.id)

        if hasattr(node.data, "simulation_id") and node.data.simulation_id:
            # Case 1: Node has simulation_id - copy simulation template
            try:
                simulation_path = PathFinder.get_simulation_path(
                    simulation_id=node.data.simulation_id, sim_global=sim_global
                )

                # Validate simulation exists (check for metadata file as indicator)
                metadata_path = simulation_path / FileConstants.METADATA_SUFFIX
                if not DataLoader.check_file_exists(metadata_path):
                    self._raise_simulation_not_found_error(node.data.simulation_id, simulation_path)

                # Copy simulation template to node directory
                DataLoader.copy_directory(source=simulation_path, destination=node_path)

            except Exception as e:
                # Fail fast - don't create inconsistent state
                self._raise_copy_template_error(e)
        else:
            # Case 2: No simulation_id - create empty node with initial files
            self._initialize_node_directory(node.id)

        return node

    def insert_node_from_scratch(
        self,
        GraphNode: GraphNode,
        nodeProperties: nodeProperties_simulation,
        nodeMetadata: nodeMetadata_simulation,
        repo_link: Optional[str] = None,
    ) -> GraphNode:
        """
        Inserts a new node into the graph from scratch, creating all necessary files and directories.

        Args:
            GraphNode: The graph node to insert
            nodeProperties: Properties configuration for the node
            nodeMetadata: Metadata configuration for the node
            repo_link: Optional repository URL to clone into the source directory

        Returns:
            The inserted GraphNode
        """

        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX
        graph = Graph.from_file(graph_file_path)

        # Create the new node
        graph.add_node(GraphNode)

        # Save the updated graph
        graph.save_to_file(graph_file_path)

        # Get node path
        node_path = PathFinder.get_node_path(self.project, GraphNode.id)

        try:
            # Create the node directory structure
            self._create_node_from_scratch(node_path, nodeProperties, nodeMetadata, repo_link)
        except Exception as e:
            # Clean up on failure
            with contextlib.suppress(Exception):
                DataLoader.remove_directory(node_path)
            msg = f"Failed to create node from scratch: {e}"
            raise ValueError(msg) from e

        return GraphNode

    def update_node_position(self, node: GraphNode) -> GraphNode:
        """
        Updates a node's position in the graph.json file.

        Args:
            node: The node with updated position

        Returns:
            The updated node
        """
        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX
        graph = Graph.from_file(graph_file_path)

        # Update the node in the graph
        graph.add_node(node)  # add_node also updates existing nodes

        # Save updated graph
        graph.save_to_file(graph_file_path)

        return node

    def delete_node(self, node_id: str) -> None:
        """
        Deletes a node from the graph and removes its directory.

        Args:
            node_id: ID of the node to delete
        """
        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX
        graph = Graph.from_file(graph_file_path)

        # Remove node from graph (this also removes connected edges)
        graph.remove_node(node_id)

        # Save updated graph
        graph.save_to_file(graph_file_path)

        # Remove node directory
        node_path = PathFinder.get_node_path(self.project, node_id)
        try:
            DataLoader.remove_directory(node_path)
        except Exception as e:
            print(f"Warning: Could not remove node directory {node_path}: {e!s}")

    def upsert_edge(self, edge: GraphEdge) -> GraphEdge:
        """
        Adds or updates an edge in the graph.json file.

        Args:
            edge: The edge to upsert

        Returns:
            The upserted edge
        """
        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX
        graph = Graph.from_file(graph_file_path)

        # Add edge to graph
        graph.add_edge(edge)

        # Save updated graph
        graph.save_to_file(graph_file_path)

        return edge

    def delete_edge(self, edge_id: str) -> None:
        """
        Deletes an edge from the graph.json file.

        Args:
            edge_id: ID of the edge to delete
        """
        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX
        graph = Graph.from_file(graph_file_path)

        # Remove edge from graph
        graph.remove_edge(edge_id)

        # Save updated graph
        graph.save_to_file(graph_file_path)

    def _ensure_graph_file_exists(self) -> None:
        """
        Ensures the graph.json file exists, creating an empty one if needed.
        """
        project_path = PathFinder.get_project_path(self.project)
        graph_file_path = project_path / FileConstants.GRAPH_SUFFIX

        if not graph_file_path.exists():
            empty_graph = Graph()
            empty_graph.save_to_file(graph_file_path)

    def _initialize_node_directory(self, node_id: str) -> None:
        """
        Initialize a node directory with default files.
        Similar to how _create_new_project creates project files.

        Args:
            node_id: The ID of the node to initialize
        """
        node_path = PathFinder.get_node_path(self.project, node_id)

        # Create the node directory
        DataWriter.create_directory(node_path)

        # Create default files (following project pattern)
        # 1. Empty parameters.json (for node configuration)
        empty_params: dict[str, dict] = {"metadata": {}, "parameters": {}}
        params_path = node_path / FileConstants.PARAMETERS_SUFFIX
        DataWriter.write_json(params_path, empty_params)

        # 2. Empty properties.yaml (for node properties)
        empty_properties: dict[str, dict] = {"properties": {}}
        properties_path = node_path / FileConstants.PROPERTIES_SUFFIX
        DataWriter.write_yaml(properties_path, empty_properties)

    # TODO: Much sophisticated handler should be created in a new module
    def _create_node_from_scratch(
        self,
        node_path: UPath,
        nodeProperties: nodeProperties_simulation,
        nodeMetadata: nodeMetadata_simulation,
        repo_link: Optional[str] = None,
    ) -> None:
        """
        Create a complete node directory structure from scratch.

        Args:
            node_path: Path where the node should be created
            nodeProperties: Properties configuration for the node
            nodeMetadata: Metadata configuration for the node
            repo_link: Optional repository URL to clone into the source directory
        """
        # Create the node directory
        DataWriter.create_directory(node_path)

        # Validate and handle missing fields
        self._validate_and_warn_missing_fields(nodeProperties, nodeMetadata)

        # Set the filepath for the models to save in the correct location
        nodeProperties._filepath = node_path / FileConstants.PROPERTIES_SUFFIX
        nodeMetadata._filepath = node_path / FileConstants.METADATA_SUFFIX

        # Create properties.yaml file
        nodeProperties.save(node_path)

        # Create metadata.yaml file
        nodeMetadata.save(node_path)

        # Create source directory
        source_path = node_path / "source"
        DataWriter.create_directory(source_path)

        # Clone repository if provided
        if repo_link:
            self._clone_repository(repo_link, source_path)

    def _validate_and_warn_missing_fields(
        self, nodeProperties: nodeProperties_simulation, nodeMetadata: nodeMetadata_simulation
    ) -> None:
        """
        Validate required fields and warn about missing optional fields.

        Args:
            nodeProperties: Properties to validate
            nodeMetadata: Metadata to validate
        """
        # Check required fields for nodeProperties
        required_props = ["container_image", "simulation_mount_path"]
        for field in required_props:
            if not getattr(nodeProperties, field, None):
                print(f"Warning: Required field '{field}' is missing or empty in nodeProperties")

        # Check required fields for nodeMetadata
        required_metadata = ["name", "id", "description", "version", "authors"]
        for field in required_metadata:
            value = getattr(nodeMetadata, field, None)
            if not value or (isinstance(value, list) and len(value) == 0):
                print(f"Warning: Required field '{field}' is missing or empty in nodeMetadata")

        # Warn about optional fields that might be important
        optional_fields = {
            "nodeProperties": ["image_name", "last_run"],
            "nodeMetadata": ["date", "code_url", "paper_url", "tags"],
        }

        for field in optional_fields["nodeProperties"]:
            if not getattr(nodeProperties, field, None):
                print(f"Info: Optional field '{field}' not provided in nodeProperties")

        for field in optional_fields["nodeMetadata"]:
            value = getattr(nodeMetadata, field, None)
            if not value or (isinstance(value, list) and len(value) == 0):
                print(f"Info: Optional field '{field}' not provided in nodeMetadata")

    def _clone_repository(self, repo_link: str, source_path: UPath) -> None:
        """
        Clone a repository into the source directory.

        Args:
            repo_link: URL of the repository to clone
            source_path: Path where the repository should be cloned
        """
        try:
            # Validate the repo_link format
            if not repo_link.strip():
                print("Warning: Empty repository link provided, skipping clone")
                return

            # Validate URL format for security
            parsed_url = urlparse(repo_link)
            if not parsed_url.scheme or parsed_url.scheme not in ("http", "https", "git", "ssh"):
                print(f"Warning: Invalid repository URL scheme: {repo_link}")
                return

            # Check if git is available
            git_path = shutil.which("git")
            if not git_path:
                print("Warning: git command not found. Please ensure git is installed and in PATH")
                return

            print(f"Cloning repository {repo_link} into {source_path}")

            # Use subprocess to clone the repository with validated git path
            subprocess.run(  # noqa: S603
                [git_path, "clone", repo_link, str(source_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minute timeout
            )

            print(f"Successfully cloned repository: {repo_link}")

        except subprocess.TimeoutExpired:
            print(f"Warning: Repository clone timed out for {repo_link}")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to clone repository {repo_link}: {e.stderr}")
        except Exception as e:
            print(f"Warning: Unexpected error cloning repository {repo_link}: {e}")

    def _raise_simulation_not_found_error(self, simulation_id: str, simulation_path: UPath) -> None:
        """Raise error when simulation is not found."""
        msg = (
            f"Simulation '{simulation_id}' not found at {simulation_path}. "
            "Please ensure the simulation exists or create a node without a simulation_id."
        )
        raise ValueError(msg)

    def _raise_copy_template_error(self, error: Exception) -> None:
        """Raise error when copying simulation template fails."""
        raise ValueError() from error
