"""
Local filesystem-based graph backend interface.

This module provides the local backend interface for graph operations,
wrapping the core GraphProcessor with backend-specific functionality.
"""

from fluidize.core.modules.graph.processor import GraphProcessor
from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
from fluidize.core.types.project import ProjectSummary


class LocalGraphProcessor:
    """
    Local filesystem-based graph processor backend.

    This class provides a clean interface for graph operations using the local backend,
    wrapping the core GraphProcessor functionality.
    """

    def __init__(self) -> None:
        """Initialize the local graph processor."""
        pass

    def get_graph(self, project: ProjectSummary) -> GraphData:
        """
        Get the complete graph for a project.

        Args:
            project: The project to get the graph for

        Returns:
            GraphData containing all nodes and edges
        """
        processor = GraphProcessor(project)
        return processor.get_graph()

    def insert_node(self, project: ProjectSummary, node: GraphNode, sim_global: bool = True) -> GraphNode:
        """
        Insert a new node into the project graph.

        Args:
            project: The project to add the node to
            node: The node to insert
            sim_global: Whether to use global simulations (placeholder for future)

        Returns:
            The inserted node
        """
        processor = GraphProcessor(project)
        return processor.insert_node(node, sim_global)

    def update_node_position(self, project: ProjectSummary, node: GraphNode) -> GraphNode:
        """
        Update a node's position in the graph.

        Args:
            project: The project containing the node
            node: The node with updated position

        Returns:
            The updated node
        """
        processor = GraphProcessor(project)
        return processor.update_node_position(node)

    def delete_node(self, project: ProjectSummary, node_id: str) -> None:
        """
        Delete a node from the project graph.

        Args:
            project: The project containing the node
            node_id: ID of the node to delete
        """
        processor = GraphProcessor(project)
        processor.delete_node(node_id)

    def upsert_edge(self, project: ProjectSummary, edge: GraphEdge) -> GraphEdge:
        """
        Add or update an edge in the project graph.

        Args:
            project: The project containing the graph
            edge: The edge to upsert

        Returns:
            The upserted edge
        """
        processor = GraphProcessor(project)
        return processor.upsert_edge(edge)

    def delete_edge(self, project: ProjectSummary, edge_id: str) -> None:
        """
        Delete an edge from the project graph.

        Args:
            project: The project containing the edge
            edge_id: ID of the edge to delete
        """
        processor = GraphProcessor(project)
        processor.delete_edge(edge_id)

    def ensure_graph_initialized(self, project: ProjectSummary) -> None:
        """
        Ensure the project has a graph.json file initialized.

        Args:
            project: The project to initialize the graph for
        """
        processor = GraphProcessor(project)
        processor._ensure_graph_file_exists()
