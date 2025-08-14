"""Unit tests for Graph model - core graph data structure and operations."""

import tempfile
from pathlib import Path

import pytest

from fluidize.core.modules.graph.model import Graph
from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
from tests.fixtures.sample_graphs import SampleGraphs


class TestGraph:
    """Test suite for Graph model class."""

    def test_init_empty(self):
        """Test Graph initialization with no nodes or edges."""
        graph = Graph()

        assert len(graph._nodes) == 0
        assert len(graph._edges) == 0

    def test_init_with_nodes(self):
        """Test Graph initialization with nodes."""
        nodes = SampleGraphs.sample_nodes()[:2]
        graph = Graph(nodes=nodes)

        assert len(graph._nodes) == 2
        assert nodes[0].id in graph._nodes
        assert nodes[1].id in graph._nodes
        assert graph._nodes[nodes[0].id] == nodes[0]

    def test_init_with_edges(self):
        """Test Graph initialization with edges."""
        edges = SampleGraphs.sample_edges()[:2]
        graph = Graph(edges=edges)

        assert len(graph._edges) == 2
        assert edges[0].id in graph._edges
        assert edges[1].id in graph._edges
        assert graph._edges[edges[0].id] == edges[0]

    def test_init_with_nodes_and_edges(self):
        """Test Graph initialization with both nodes and edges."""
        nodes = SampleGraphs.sample_nodes()[:2]
        edges = SampleGraphs.sample_edges()[:1]
        graph = Graph(nodes=nodes, edges=edges)

        assert len(graph._nodes) == 2
        assert len(graph._edges) == 1

    def test_add_node_new(self):
        """Test adding a new node."""
        graph = Graph()
        node = SampleGraphs.sample_nodes()[0]

        graph.add_node(node)

        assert node.id in graph._nodes
        assert graph._nodes[node.id] == node

    def test_add_node_update_existing(self):
        """Test updating an existing node."""
        node = SampleGraphs.sample_nodes()[0]
        graph = Graph(nodes=[node])

        # Create updated version
        updated_node = GraphNode(id=node.id, position=node.position, data=node.data, type="updated-type")

        graph.add_node(updated_node)

        assert graph._nodes[node.id] == updated_node
        assert graph._nodes[node.id].type == "updated-type"

    def test_remove_node_exists(self):
        """Test removing an existing node."""
        nodes = SampleGraphs.sample_nodes()[:2]
        graph = Graph(nodes=nodes)
        node_to_remove = nodes[0]

        graph.remove_node(node_to_remove.id)

        assert node_to_remove.id not in graph._nodes
        assert len(graph._nodes) == 1

    def test_remove_node_not_exists(self):
        """Test removing a non-existent node."""
        graph = Graph()

        # Should not raise error
        graph.remove_node("non-existent-id")

        assert len(graph._nodes) == 0

    def test_remove_node_with_connected_edges(self):
        """Test removing a node also removes connected edges."""
        # Create a connected graph
        graph_data = SampleGraphs.connected_graph()
        graph = Graph(nodes=graph_data.nodes, edges=graph_data.edges)

        # Remove a node that has connected edges
        node_id = "node-1"  # This node is connected in the sample

        graph.remove_node(node_id)

        assert node_id not in graph._nodes
        # Connected edges should be removed
        for edge in graph._edges.values():
            assert edge.source != node_id
            assert edge.target != node_id

    def test_add_edge_new(self):
        """Test adding a new edge."""
        graph = Graph()
        # First add nodes that the edge connects
        nodes = SampleGraphs.sample_nodes()[:2]
        for node in nodes:
            graph.add_node(node)

        # Create edge connecting existing nodes
        from fluidize.core.types.graph import GraphEdge

        edge = GraphEdge(id="test-edge", source=nodes[0].id, target=nodes[1].id, type="data-flow")

        graph.add_edge(edge)

        assert edge.id in graph._edges
        assert graph._edges[edge.id] == edge

    def test_add_edge_update_existing(self):
        """Test updating an existing edge."""
        # First create nodes
        nodes = SampleGraphs.sample_nodes()[:2]
        graph = Graph(nodes=nodes)

        # Create initial edge
        from fluidize.core.types.graph import GraphEdge

        edge = GraphEdge(id="update-edge", source=nodes[0].id, target=nodes[1].id, type="original-type")
        graph.add_edge(edge)

        # Create updated version
        updated_edge = GraphEdge(id=edge.id, source=edge.source, target=edge.target, type="updated-edge-type")

        graph.add_edge(updated_edge)

        assert graph._edges[edge.id] == updated_edge
        assert graph._edges[edge.id].type == "updated-edge-type"

    def test_remove_edge_exists(self):
        """Test removing an existing edge."""
        edges = SampleGraphs.sample_edges()[:2]
        graph = Graph(edges=edges)
        edge_to_remove = edges[0]

        graph.remove_edge(edge_to_remove.id)

        assert edge_to_remove.id not in graph._edges
        assert len(graph._edges) == 1

    def test_remove_edge_not_exists(self):
        """Test removing a non-existent edge."""
        graph = Graph()

        # Should not raise error
        graph.remove_edge("non-existent-id")

        assert len(graph._edges) == 0

    def test_heal_removes_orphaned_edges(self):
        """Test that heal() removes edges connected to non-existent nodes."""
        # Create graph with nodes and edges
        nodes = SampleGraphs.two_node_graph().nodes
        edges = [
            GraphEdge(id="valid-edge", source=nodes[0].id, target=nodes[1].id, type="data-flow"),
            GraphEdge(id="orphaned-edge-1", source="non-existent-source", target=nodes[1].id, type="data-flow"),
            GraphEdge(id="orphaned-edge-2", source=nodes[0].id, target="non-existent-target", type="data-flow"),
        ]

        graph = Graph(nodes=nodes, edges=edges)
        assert len(graph._edges) == 3

        graph.heal()

        # Only the valid edge should remain
        assert len(graph._edges) == 1
        assert "valid-edge" in graph._edges
        assert "orphaned-edge-1" not in graph._edges
        assert "orphaned-edge-2" not in graph._edges

    def test_heal_no_orphaned_edges(self):
        """Test heal() when no orphaned edges exist."""
        graph_data = SampleGraphs.connected_graph()
        graph = Graph(nodes=graph_data.nodes, edges=graph_data.edges)
        original_edge_count = len(graph._edges)

        graph.heal()

        # No edges should be removed
        assert len(graph._edges) == original_edge_count

    def test_to_graph_data(self):
        """Test conversion to GraphData."""
        graph_data = SampleGraphs.complex_graph()
        graph = Graph(nodes=graph_data.nodes, edges=graph_data.edges)

        result = graph.to_graph_data()

        assert isinstance(result, GraphData)
        assert len(result.nodes) == len(graph_data.nodes)
        assert len(result.edges) == len(graph_data.edges)

        # Verify all nodes are included
        result_node_ids = {node.id for node in result.nodes}
        expected_node_ids = {node.id for node in graph_data.nodes}
        assert result_node_ids == expected_node_ids

        # Verify all edges are included
        result_edge_ids = {edge.id for edge in result.edges}
        expected_edge_ids = {edge.id for edge in graph_data.edges}
        assert result_edge_ids == expected_edge_ids

    def test_to_graph_data_empty(self):
        """Test conversion to GraphData when graph is empty."""
        graph = Graph()

        result = graph.to_graph_data()

        assert isinstance(result, GraphData)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_from_file_success(self):
        """Test loading graph from file."""
        graph_data = SampleGraphs.connected_graph()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            # Write graph data to file
            import json

            json.dump(
                {
                    "nodes": [node.model_dump() for node in graph_data.nodes],
                    "edges": [edge.model_dump() for edge in graph_data.edges],
                },
                tmp_file,
            )
            tmp_path = Path(tmp_file.name)

        try:
            graph = Graph.from_file(tmp_path)

            assert len(graph._nodes) == len(graph_data.nodes)
            assert len(graph._edges) == len(graph_data.edges)

            # Verify node IDs match
            for node in graph_data.nodes:
                assert node.id in graph._nodes

        finally:
            tmp_path.unlink()

    def test_from_file_not_exists(self):
        """Test loading graph from non-existent file."""
        non_existent_path = Path("/non/existent/path.json")

        graph = Graph.from_file(non_existent_path)

        # Should return empty graph
        assert len(graph._nodes) == 0
        assert len(graph._edges) == 0

    def test_from_file_invalid_json(self):
        """Test loading graph from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            tmp_file.write("invalid json content")
            tmp_path = Path(tmp_file.name)

        try:
            # This should raise a JSONDecodeError, not return an empty graph
            with pytest.raises((ValueError, TypeError)):  # JSON parsing errors
                Graph.from_file(tmp_path)

        finally:
            tmp_path.unlink()

    def test_save_to_file_success(self):
        """Test saving graph to file."""
        graph_data = SampleGraphs.connected_graph()
        graph = Graph(nodes=graph_data.nodes, edges=graph_data.edges)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            graph.save_to_file(tmp_path)

            # Verify file was created and contains correct data
            assert tmp_path.exists()

            # Load and verify content
            import json

            with open(tmp_path) as f:
                data = json.load(f)

            assert "nodes" in data
            assert "edges" in data
            assert len(data["nodes"]) == len(graph_data.nodes)
            assert len(data["edges"]) == len(graph_data.edges)

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_save_to_file_creates_directory(self):
        """Test that save_to_file creates parent directories."""
        graph = Graph()

        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_path = Path(tmp_dir) / "subdir" / "graph.json"

            graph.save_to_file(nested_path)

            assert nested_path.exists()
            assert nested_path.parent.exists()

    def test_file_roundtrip(self):
        """Test saving and loading a graph maintains data integrity."""
        original_graph_data = SampleGraphs.complex_graph()
        original_graph = Graph(nodes=original_graph_data.nodes, edges=original_graph_data.edges)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Save and load
            original_graph.save_to_file(tmp_path)
            loaded_graph = Graph.from_file(tmp_path)

            # Compare data
            original_data = original_graph.to_graph_data()
            loaded_data = loaded_graph.to_graph_data()

            assert len(loaded_data.nodes) == len(original_data.nodes)
            assert len(loaded_data.edges) == len(original_data.edges)

            # Verify all nodes match
            original_node_ids = {node.id for node in original_data.nodes}
            loaded_node_ids = {node.id for node in loaded_data.nodes}
            assert loaded_node_ids == original_node_ids

            # Verify all edges match
            original_edge_ids = {edge.id for edge in original_data.edges}
            loaded_edge_ids = {edge.id for edge in loaded_data.edges}
            assert loaded_edge_ids == original_edge_ids

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_graph_operations_sequence(self):
        """Test sequence of graph operations."""
        graph = Graph()
        nodes = SampleGraphs.sample_nodes()[:2]

        # Add nodes
        for node in nodes:
            graph.add_node(node)

        assert len(graph._nodes) == 2

        # Add edge connecting the nodes
        edge = GraphEdge(id="connecting-edge", source=nodes[0].id, target=nodes[1].id, type="connection")
        graph.add_edge(edge)

        assert len(graph._edges) == 1

        # Remove one node (should also remove the edge)
        graph.remove_node(nodes[0].id)

        assert len(graph._nodes) == 1
        assert nodes[0].id not in graph._nodes
        assert len(graph._edges) == 0  # Edge should be removed

    def test_duplicate_ids_handling(self):
        """Test that duplicate IDs are handled by replacement."""
        node1 = SampleGraphs.sample_nodes()[0]
        node2 = GraphNode(
            id=node1.id,  # Same ID
            position=node1.position,
            data=node1.data,
            type="different-type",
        )

        graph = Graph()
        graph.add_node(node1)
        graph.add_node(node2)  # Should replace node1

        assert len(graph._nodes) == 1
        assert graph._nodes[node1.id].type == "different-type"
