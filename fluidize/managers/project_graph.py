"""
Project-scoped graph manager for user-friendly graph operations.
"""

from typing import Any, Optional

from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
from fluidize.core.types.node import nodeMetadata_simulation, nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary


class ProjectGraph:
    """
    Graph manager for a specific project.

    Provides graph operations like adding nodes/edges without requiring
    project context on each method call.
    """

    def __init__(self, backend: Any, project: ProjectSummary) -> None:
        """
        Initialize project-scoped graph manager.

        Args:
            backend: Backend adapter (FluidizeSDK or LocalBackend)
            project: The project this graph manager is bound to
        """
        self.backend = backend
        self.project = project

        # Ensure graph is initialized for this project
        if hasattr(self.backend, "graph") and hasattr(self.backend.graph, "ensure_graph_initialized"):
            self.backend.graph.ensure_graph_initialized(self.project)

    def get(self) -> GraphData:
        """
        Get the complete graph for this project.

        Returns:
            GraphData containing all nodes and edges for this project
        """
        return self.backend.graph.get_graph(self.project)  # type: ignore[no-any-return]

    def add_node(self, node: GraphNode, sim_global: bool = True) -> GraphNode:
        """
        Add a new node to this project's graph.

        Args:
            node: The node to insert
            sim_global: Whether to use global simulations (placeholder for future)

        Returns:
            The inserted node
        """
        return self.backend.graph.insert_node(self.project, node, sim_global)  # type: ignore[no-any-return]

    def add_node_from_scratch(
        self,
        node: GraphNode,
        node_properties: nodeProperties_simulation,
        node_metadata: nodeMetadata_simulation,
        repo_link: Optional[str] = None,
    ) -> GraphNode:
        """
        Add a new node to this project's graph from scratch, creating all necessary files and directories.

        Args:
            node: The graph node to insert
            node_properties: Properties configuration for the node
            node_metadata: Metadata configuration for the node
            repo_link: Optional repository URL to clone into the source directory

        Returns:
            The inserted node
        """
        return self.backend.graph.insert_node_from_scratch(  # type: ignore[no-any-return]
            self.project, node, node_properties, node_metadata, repo_link
        )

    def update_node_position(self, node: GraphNode) -> GraphNode:
        """
        Update a node's position in this project's graph.

        Args:
            node: The node with updated position

        Returns:
            The updated node
        """
        return self.backend.graph.update_node_position(self.project, node)  # type: ignore[no-any-return]

    def delete_node(self, node_id: str) -> None:
        """
        Delete a node from this project's graph.

        Args:
            node_id: ID of the node to delete
        """
        self.backend.graph.delete_node(self.project, node_id)

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """
        Add or update an edge in this project's graph.

        Args:
            edge: The edge to upsert

        Returns:
            The upserted edge
        """
        return self.backend.graph.upsert_edge(self.project, edge)  # type: ignore[no-any-return]

    def delete_edge(self, edge_id: str) -> None:
        """
        Delete an edge from this project's graph.

        Args:
            edge_id: ID of the edge to delete
        """
        self.backend.graph.delete_edge(self.project, edge_id)

    def show(self) -> str:
        """
        Get ASCII visualization of this project's graph.

        Returns:
            ASCII string representation of the graph structure
        """
        return self.backend.graph.show_graph_ascii(self.project)  # type: ignore[no-any-return]
