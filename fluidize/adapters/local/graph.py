"""
Local filesystem-based graph adapter interface.

This module provides the local adapter interface for graph operations,
wrapping the core GraphProcessor with adapter-specific functionality.
"""

from typing import Optional

from fluidize.core.modules.graph.processor import GraphProcessor
from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
from fluidize.core.types.node import nodeMetadata_simulation, nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary


class GraphHandler:
    """
    Local filesystem-based graph processor adapter.

    This class provides a clean interface for graph operations using the local adapter,
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

    def insert_node_from_scratch(
        self,
        project: ProjectSummary,
        GraphNode: GraphNode,
        nodeProperties: nodeProperties_simulation,
        nodeMetadata: nodeMetadata_simulation,
        repo_link: Optional[str] = None,
    ) -> GraphNode:
        """
        Insert a new node into the project graph from scratch.

        Args:
            project: The project to add the node to
            nodeProperties: The properties of the node to insert
            sim_global: Whether to use global simulations (placeholder for future)

        Returns:
            The inserted node
        """
        processor = GraphProcessor(project)
        return processor.insert_node_from_scratch(GraphNode, nodeProperties, nodeMetadata, repo_link)

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

    def show_graph_ascii(self, project: ProjectSummary) -> str:
        """
        Get ASCII representation of the project graph.

        Args:
            project: The project to visualize

        Returns:
            ASCII string representation of the graph
        """
        processor = GraphProcessor(project)
        graph_data = processor.get_graph()

        # Create Graph model from the data to use ASCII visualization
        from fluidize.core.modules.graph.model import Graph

        graph = Graph(nodes=graph_data.nodes, edges=graph_data.edges)

        return graph.to_ascii()
