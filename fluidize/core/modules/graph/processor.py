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
        Inserts a node from the list of simulations.

        Args:
            node: The node to insert
            sim_global: Whether to use global simulations (placeholder for future implementation)

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

        # Copy simulation template to node directory (when simulations are available)
        try:
            if hasattr(node.data, "simulation_id") and node.data.simulation_id:
                simulation_path = PathFinder.get_simulation_path(
                    simulation_id=node.data.simulation_id, sim_global=sim_global
                )
                node_path = PathFinder.get_node_path(self.project, node.id)

                # Copy simulation template to create the node
                DataLoader.copy_directory(source=simulation_path, destination=node_path)
        except Exception as e:
            print(f"Warning: Could not copy simulation template: {e!s}")
            # Continue without template copying - this is expected until simulations are implemented

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
