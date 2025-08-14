"""Sample graph data and fixtures for testing."""

from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode, Position, graphNodeData


class SampleGraphs:
    """Collection of sample graph data for testing."""

    @staticmethod
    def empty_graph() -> GraphData:
        """Empty graph with no nodes or edges."""
        return GraphData(nodes=[], edges=[])

    @staticmethod
    def single_node_graph() -> GraphData:
        """Graph with a single isolated node."""
        node = GraphNode(
            id="single-node",
            position=Position(x=100.0, y=200.0),
            data=graphNodeData(label="Single Test Node", simulation_id=""),
            type="simulation",
        )
        return GraphData(nodes=[node], edges=[])

    @staticmethod
    def two_node_graph() -> GraphData:
        """Graph with two unconnected nodes."""
        node1 = GraphNode(
            id="node-1",
            position=Position(x=100.0, y=200.0),
            data=graphNodeData(label="First Node", simulation_id=""),
            type="simulation",
        )
        node2 = GraphNode(
            id="node-2",
            position=Position(x=300.0, y=400.0),
            data=graphNodeData(label="Second Node", simulation_id=""),
            type="simulation",
        )
        return GraphData(nodes=[node1, node2], edges=[])

    @staticmethod
    def connected_graph() -> GraphData:
        """Graph with two connected nodes."""
        nodes = SampleGraphs.two_node_graph().nodes
        edge = GraphEdge(id="edge-1-2", source="node-1", target="node-2", type="data-flow")
        return GraphData(nodes=nodes, edges=[edge])

    @staticmethod
    def complex_graph() -> GraphData:
        """More complex graph with multiple nodes and edges."""
        nodes = [
            GraphNode(
                id="input-node",
                position=Position(x=50.0, y=100.0),
                data=graphNodeData(label="Input Node", simulation_id=""),
                type="input",
            ),
            GraphNode(
                id="process-node-1",
                position=Position(x=200.0, y=100.0),
                data=graphNodeData(label="Process Node 1", simulation_id=""),
                type="simulation",
            ),
            GraphNode(
                id="process-node-2",
                position=Position(x=200.0, y=300.0),
                data=graphNodeData(label="Process Node 2", simulation_id=""),
                type="simulation",
            ),
            GraphNode(
                id="output-node",
                position=Position(x=400.0, y=200.0),
                data=graphNodeData(label="Output Node", simulation_id=""),
                type="output",
            ),
        ]

        edges = [
            GraphEdge(id="input-to-process-1", source="input-node", target="process-node-1", type="data-flow"),
            GraphEdge(id="input-to-process-2", source="input-node", target="process-node-2", type="data-flow"),
            GraphEdge(id="process-1-to-output", source="process-node-1", target="output-node", type="data-flow"),
            GraphEdge(id="process-2-to-output", source="process-node-2", target="output-node", type="data-flow"),
        ]

        return GraphData(nodes=nodes, edges=edges)

    @staticmethod
    def sample_nodes() -> list[GraphNode]:
        """Collection of individual nodes for testing."""
        return [
            GraphNode(
                id="test-node-basic",
                position=Position(x=0.0, y=0.0),
                data=graphNodeData(label="Basic Test Node", simulation_id=""),
                type="simulation",
            ),
            GraphNode(
                id="test-node-positioned",
                position=Position(x=150.5, y=275.25),
                data=graphNodeData(label="Positioned Node", simulation_id=""),
                type="simulation",
            ),
            GraphNode(
                id="test-node-special-chars",
                position=Position(x=100.0, y=100.0),
                data=graphNodeData(label="Node with Special Chars: !@#$%", simulation_id=""),
                type="custom",
            ),
        ]

    @staticmethod
    def sample_edges() -> list[GraphEdge]:
        """Collection of individual edges for testing."""
        return [
            GraphEdge(id="edge-basic", source="node-a", target="node-b", type="data-flow"),
            GraphEdge(id="edge-control", source="node-b", target="node-c", type="control-flow"),
            GraphEdge(id="edge-custom", source="node-c", target="node-a", type="custom-connection"),
        ]

    @staticmethod
    def invalid_graph_data() -> list[dict]:
        """Invalid graph data for error testing."""
        return [
            # Invalid node - missing required fields
            {"nodes": [{"id": "incomplete-node"}], "edges": []},
            # Invalid edge - references non-existent nodes
            {
                "nodes": [],
                "edges": [
                    {
                        "id": "orphan-edge",
                        "source": "non-existent-source",
                        "target": "non-existent-target",
                        "type": "data-flow",
                    }
                ],
            },
            # Duplicate node IDs
            {
                "nodes": [
                    {
                        "id": "duplicate-id",
                        "position": {"x": 0.0, "y": 0.0},
                        "data": {"label": "First", "simulation_id": "sim-1"},
                        "type": "simulation",
                    },
                    {
                        "id": "duplicate-id",
                        "position": {"x": 100.0, "y": 100.0},
                        "data": {"label": "Second", "simulation_id": "sim-2"},
                        "type": "simulation",
                    },
                ],
                "edges": [],
            },
        ]

    @staticmethod
    def node_update_data() -> dict:
        """Sample data for node position updates."""
        return {
            "id": "node-to-update",
            "position": Position(x=500.0, y=600.0),
            "data": graphNodeData(label="Updated Node Label", simulation_id=""),
            "type": "updated-type",
        }
