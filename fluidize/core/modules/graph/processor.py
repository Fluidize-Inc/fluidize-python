"""
Local filesystem-based graph processor.

This module provides the core business logic for graph operations using
the local filesystem, without any cloud or Firebase dependencies.
"""

from fluidize.core.constants import FileConstants
from fluidize.core.modules.graph.model import Graph
from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
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

    def _raise_simulation_not_found_error(self, simulation_id: str, simulation_path) -> None:
        """Raise error when simulation is not found."""
        msg = (
            f"Simulation '{simulation_id}' not found at {simulation_path}. "
            "Please ensure the simulation exists or create a node without a simulation_id."
        )
        raise ValueError(msg)

    def _raise_copy_template_error(self, error: Exception) -> None:
        """Raise error when copying simulation template fails."""
        raise ValueError() from error
