"""
Graph model for fluidize-python.

This module provides an intelligent, in-memory representation of the simulation graph
with filesystem-based I/O capabilities.
"""

import json
from collections import OrderedDict
from pathlib import Path
from typing import Union

from asciitree import LeftAligned  # type: ignore[import-untyped]

from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode


class InvalidEdgeError(ValueError):
    """Raised when trying to add an edge connected to non-existent nodes."""

    def __init__(self) -> None:
        super().__init__("Cannot add edge connected to non-existent node")


class Graph:
    """
    An intelligent, in-memory representation of the simulation graph.
    This class contains all the logic for manipulating the graph structure
    and handling file-based I/O.
    """

    def __init__(self, nodes: Union[list[GraphNode], None] = None, edges: Union[list[GraphEdge], None] = None):
        self._nodes: dict[str, GraphNode] = {node.id: node for node in (nodes or [])}
        self._edges: dict[str, GraphEdge] = {edge.id: edge for edge in (edges or [])}

    @property
    def nodes(self) -> list[GraphNode]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[GraphEdge]:
        return list(self._edges.values())

    def add_node(self, node: GraphNode) -> None:
        """Adds a node to the graph."""
        self._nodes[node.id] = node

    def remove_node(self, node_id: str) -> None:
        """
        Removes a node and any edges connected to it.
        This is the core logic for offline/file-based manipulation.
        """
        if node_id in self._nodes:
            del self._nodes[node_id]
            # Remove connected edges
            connected_edge_ids = [edge.id for edge in self.edges if edge.source == node_id or edge.target == node_id]
            for edge_id in connected_edge_ids:
                self.remove_edge(edge_id)

    def add_edge(self, edge: GraphEdge) -> None:
        """Adds an edge to the graph."""
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise InvalidEdgeError()
        self._edges[edge.id] = edge

    def remove_edge(self, edge_id: str) -> None:
        """Removes an edge from the graph."""
        if edge_id in self._edges:
            del self._edges[edge_id]

    def validate(self) -> bool:
        """Checks for graph inconsistencies, like orphaned edges."""
        return all(edge.source in self._nodes and edge.target in self._nodes for edge in self.edges)

    def heal(self) -> None:
        """Destructively removes any orphaned edges."""
        orphaned_edge_ids = [edge.id for edge in self.edges if not self._validate_edge(edge)]
        for edge_id in orphaned_edge_ids:
            self.remove_edge(edge_id)

    def _validate_edge(self, edge: GraphEdge) -> bool:
        """Validates a single edge."""
        return edge.source in self._nodes and edge.target in self._nodes

    def to_graph_data(self) -> GraphData:
        """Exports the current state to a Pydantic GraphData model."""
        return GraphData(nodes=self.nodes, edges=self.edges)

    @classmethod
    def from_file(cls, path: Path) -> "Graph":
        """Loads a graph from a graph.json file."""
        if not path.exists():
            return cls()  # Return an empty graph if file doesn't exist

        with open(path) as f:
            data = json.load(f)

        nodes = [GraphNode(**node_data) for node_data in data.get("nodes", [])]
        edges = [GraphEdge(**edge_data) for edge_data in data.get("edges", [])]
        return cls(nodes, edges)

    def save_to_file(self, path: Path) -> None:
        """Saves the current graph state to a graph.json file."""
        graph_data = self.to_graph_data()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            # Use .model_dump(mode="json") for proper serialization of Pydantic models
            json.dump(graph_data.model_dump(mode="json"), f, indent=2)

    def to_ascii(self) -> str:
        """Generate an ASCII representation of the graph."""
        if not self.nodes:
            return "Empty graph - no nodes found."

        # Build tree structure for asciitree
        tree_data = self._build_tree_structure()

        # Render with asciitree
        tree_renderer = LeftAligned()
        result = tree_renderer(tree_data)
        return str(result)

    def _build_tree_structure(self) -> dict:
        """Build a tree structure suitable for asciitree rendering."""
        # Create adjacency map
        children_map: dict[str, list[str]] = {}
        parent_map: dict[str, str] = {}

        # Get node labels
        node_labels = {}
        for node in self.nodes:
            label = getattr(node.data, "label", node.id)
            node_labels[node.id] = label
            children_map[node.id] = []

        # Build parent-child relationships
        for edge in self.edges:
            children_map[edge.source].append(edge.target)
            parent_map[edge.target] = edge.source

        # Find root nodes (nodes with no parents)
        root_nodes = [node_id for node_id in children_map if node_id not in parent_map]

        # If no edges, show all nodes under a "Nodes" header
        if not self.edges:
            tree_data = OrderedDict()
            nodes_section: OrderedDict[str, OrderedDict] = OrderedDict()
            for node in self.nodes:
                label = getattr(node.data, "label", node.id)
                nodes_section[label] = OrderedDict()
            tree_data["Nodes (no connections)"] = nodes_section
            return tree_data

        # If no clear roots (circular graph), pick the first node
        if not root_nodes:
            root_nodes = [self.nodes[0].id] if self.nodes else []

        # Build tree recursively
        def build_subtree(node_id: str, visited: set) -> OrderedDict:
            if node_id in visited:
                return OrderedDict({"(circular reference)": OrderedDict()})

            visited.add(node_id)
            subtree = OrderedDict()

            for child_id in children_map.get(node_id, []):
                child_label = node_labels[child_id]
                subtree[child_label] = build_subtree(child_id, visited.copy())

            return subtree

        # Build the complete tree
        tree_data = OrderedDict()
        for root_id in root_nodes:
            root_label = node_labels[root_id]
            tree_data[root_label] = build_subtree(root_id, set())

        return tree_data
