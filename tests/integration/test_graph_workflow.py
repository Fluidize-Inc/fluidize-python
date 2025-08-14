"""Integration tests for complete graph workflow - client to adapter."""

import tempfile
from pathlib import Path

import pytest

from fluidize import FluidizeClient
from fluidize.core.types.graph import GraphNode, Position, graphNodeData
from fluidize.managers.project_manager import ProjectManager
from tests.fixtures.sample_graphs import SampleGraphs


class TestGraphWorkflow:
    """Integration test suite for complete graph workflows."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def client(self, temp_dir):
        """Create a FluidizeClient in local mode with temp directory."""
        # Configure global config for testing
        from fluidize.config import config

        # Store original values
        original_mode = config.mode
        original_base_path = config.local_base_path
        original_projects_path = config.local_projects_path
        original_simulations_path = config.local_simulations_path

        # Configure global config
        config.mode = "local"
        config.local_base_path = temp_dir
        config.local_projects_path = temp_dir / "projects"
        config.local_simulations_path = temp_dir / "simulations"

        # Ensure directories exist
        config.local_projects_path.mkdir(parents=True, exist_ok=True)
        config.local_simulations_path.mkdir(parents=True, exist_ok=True)

        try:
            client = FluidizeClient(mode="local")
            yield client
        finally:
            # Restore original values
            config.mode = original_mode
            config.local_base_path = original_base_path
            config.local_projects_path = original_projects_path
            config.local_simulations_path = original_simulations_path

    def test_complete_project_graph_workflow(self, client):
        """Test complete workflow from client creation to graph operations."""
        # Create a project
        project = client.projects.create(
            project_id="integration-test-project",
            label="Integration Test Project",
            description="Testing complete graph workflow",
        )

        assert isinstance(project, ProjectManager)
        assert project.id == "integration-test-project"
        assert project.label == "Integration Test Project"

        # Access graph property (should initialize empty graph)
        graph = project.graph
        assert graph is not None

        # Get initial (empty) graph
        graph_data = graph.get()
        assert len(graph_data.nodes) == 0
        assert len(graph_data.edges) == 0

        # Add a node
        node_data = graphNodeData(label="Test Node 1", simulation_id="")
        node = GraphNode(id="test-node-1", position=Position(x=100.0, y=200.0), data=node_data, type="simulation")

        added_node = graph.add_node(node)
        assert added_node.id == "test-node-1"
        assert added_node.data.label == "Test Node 1"

        # Verify graph now has the node
        updated_graph = graph.get()
        assert len(updated_graph.nodes) == 1
        assert updated_graph.nodes[0].id == "test-node-1"

        # Add another node
        node2_data = graphNodeData(label="Test Node 2", simulation_id="")
        node2 = GraphNode(id="test-node-2", position=Position(x=300.0, y=400.0), data=node2_data, type="simulation")

        graph.add_node(node2)

        # Add edge connecting the nodes
        edge = SampleGraphs.sample_edges()[0]
        edge.source = "test-node-1"
        edge.target = "test-node-2"
        edge.id = "test-edge-1-2"

        added_edge = graph.add_edge(edge)
        assert added_edge.id == "test-edge-1-2"
        assert added_edge.source == "test-node-1"
        assert added_edge.target == "test-node-2"

        # Verify final graph state
        final_graph = graph.get()
        assert len(final_graph.nodes) == 2
        assert len(final_graph.edges) == 1

        # Verify node details
        node_ids = {node.id for node in final_graph.nodes}
        assert node_ids == {"test-node-1", "test-node-2"}

        # Verify edge details
        assert final_graph.edges[0].source == "test-node-1"
        assert final_graph.edges[0].target == "test-node-2"

    def test_multiple_projects_isolation(self, client):
        """Test that graph operations are isolated between projects."""
        # Create two projects
        project1 = client.projects.create(project_id="project-1", label="First Project")
        project2 = client.projects.create(project_id="project-2", label="Second Project")

        # Add node to first project
        node1 = GraphNode(
            id="node-in-project-1",
            position=Position(x=0.0, y=0.0),
            data=graphNodeData(label="Node 1", simulation_id=""),
            type="simulation",
        )
        project1.graph.add_node(node1)

        # Add node to second project
        node2 = GraphNode(
            id="node-in-project-2",
            position=Position(x=0.0, y=0.0),
            data=graphNodeData(label="Node 2", simulation_id=""),
            type="simulation",
        )
        project2.graph.add_node(node2)

        # Verify isolation
        graph1 = project1.graph.get()
        graph2 = project2.graph.get()

        assert len(graph1.nodes) == 1
        assert len(graph2.nodes) == 1
        assert graph1.nodes[0].id == "node-in-project-1"
        assert graph2.nodes[0].id == "node-in-project-2"

    def test_node_update_operations(self, client):
        """Test node update operations in workflow."""
        project = client.projects.create(project_id="update-test-project", label="Update Test Project")

        # Add initial node
        original_node = GraphNode(
            id="update-node",
            position=Position(x=100.0, y=100.0),
            data=graphNodeData(label="Original Label", simulation_id=""),
            type="simulation",
        )
        project.graph.add_node(original_node)

        # Update node position
        updated_node = GraphNode(
            id="update-node",
            position=Position(x=500.0, y=600.0),
            data=graphNodeData(label="Updated Label", simulation_id=""),
            type="simulation",
        )

        result = project.graph.update_node_position(updated_node)
        assert result.position.x == 500.0
        assert result.position.y == 600.0

        # Verify update in graph
        graph = project.graph.get()
        assert len(graph.nodes) == 1
        node = graph.nodes[0]
        assert node.position.x == 500.0
        assert node.position.y == 600.0

    def test_node_deletion_workflow(self, client):
        """Test node deletion removes node and connected edges."""
        project = client.projects.create(project_id="delete-test-project", label="Delete Test Project")

        # Add two nodes
        node1 = GraphNode(
            id="node-to-keep",
            position=Position(x=0.0, y=0.0),
            data=graphNodeData(label="Keep Node", simulation_id=""),
            type="simulation",
        )
        node2 = GraphNode(
            id="node-to-delete",
            position=Position(x=100.0, y=100.0),
            data=graphNodeData(label="Delete Node", simulation_id=""),
            type="simulation",
        )

        project.graph.add_node(node1)
        project.graph.add_node(node2)

        # Add edge connecting them
        edge = SampleGraphs.sample_edges()[0]
        edge.id = "connecting-edge"
        edge.source = "node-to-keep"
        edge.target = "node-to-delete"
        project.graph.add_edge(edge)

        # Verify initial state
        initial_graph = project.graph.get()
        assert len(initial_graph.nodes) == 2
        assert len(initial_graph.edges) == 1

        # Delete one node
        project.graph.delete_node("node-to-delete")

        # Verify final state
        final_graph = project.graph.get()
        assert len(final_graph.nodes) == 1
        assert final_graph.nodes[0].id == "node-to-keep"
        # Connected edges should be removed by graph healing
        assert len(final_graph.edges) == 0

    def test_edge_operations_workflow(self, client):
        """Test edge addition and removal workflow."""
        project = client.projects.create(project_id="edge-test-project", label="Edge Test Project")

        # Add two nodes first
        nodes = SampleGraphs.two_node_graph().nodes
        for node in nodes:
            project.graph.add_node(node)

        # Add edge
        edge = SampleGraphs.sample_edges()[0]
        edge.source = nodes[0].id
        edge.target = nodes[1].id
        project.graph.add_edge(edge)

        # Verify edge was added
        graph_with_edge = project.graph.get()
        assert len(graph_with_edge.edges) == 1
        assert graph_with_edge.edges[0].source == nodes[0].id
        assert graph_with_edge.edges[0].target == nodes[1].id

        # Remove edge
        project.graph.delete_edge(edge.id)

        # Verify edge was removed
        graph_without_edge = project.graph.get()
        assert len(graph_without_edge.edges) == 0
        # Nodes should remain
        assert len(graph_without_edge.nodes) == 2

    def test_complex_graph_workflow(self, client):
        """Test workflow with complex graph operations."""
        project = client.projects.create(project_id="complex-test-project", label="Complex Test Project")

        # Build complex graph step by step
        complex_graph_data = SampleGraphs.complex_graph()

        # Add all nodes
        for node in complex_graph_data.nodes:
            project.graph.add_node(node)

        # Add all edges
        for edge in complex_graph_data.edges:
            project.graph.add_edge(edge)

        # Verify complete graph
        final_graph = project.graph.get()
        assert len(final_graph.nodes) == len(complex_graph_data.nodes)
        assert len(final_graph.edges) == len(complex_graph_data.edges)

        # Verify node IDs match
        final_node_ids = {node.id for node in final_graph.nodes}
        expected_node_ids = {node.id for node in complex_graph_data.nodes}
        assert final_node_ids == expected_node_ids

        # Verify edge IDs match
        final_edge_ids = {edge.id for edge in final_graph.edges}
        expected_edge_ids = {edge.id for edge in complex_graph_data.edges}
        assert final_edge_ids == expected_edge_ids

    def test_project_graph_persistence(self, client, temp_dir):
        """Test that graph data persists across client sessions."""
        project_id = "persistence-test-project"

        # First session - create and populate graph
        project1 = client.projects.create(project_id=project_id, label="Persistence Test")

        node = GraphNode(
            id="persistent-node",
            position=Position(x=100.0, y=200.0),
            data=graphNodeData(label="Persistent Node", simulation_id=""),
            type="simulation",
        )
        project1.graph.add_node(node)

        # Verify graph was created
        graph1 = project1.graph.get()
        assert len(graph1.nodes) == 1

        # Create new client (simulating new session)
        # Since the config is already configured by the fixture, just create a new client
        client2 = FluidizeClient(mode="local")

        # Retrieve same project
        project2 = client2.projects.get(project_id)

        # Verify graph data persisted
        graph2 = project2.graph.get()
        assert len(graph2.nodes) == 1
        assert graph2.nodes[0].id == "persistent-node"
        assert graph2.nodes[0].data.label == "Persistent Node"

    def test_error_handling_in_workflow(self, client):
        """Test error handling in graph workflows."""
        project = client.projects.create(project_id="error-test-project", label="Error Test Project")

        # Try to delete non-existent node (should not raise error)
        project.graph.delete_node("non-existent-node")

        # Try to delete non-existent edge (should not raise error)
        project.graph.delete_edge("non-existent-edge")

        # Graph should remain empty
        graph = project.graph.get()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_project_list_with_graphs(self, client):
        """Test listing projects that have graphs."""
        # Create multiple projects with graphs
        projects_data = [("proj-1", "Project 1"), ("proj-2", "Project 2"), ("proj-3", "Project 3")]

        created_projects = []
        for proj_id, label in projects_data:
            project = client.projects.create(project_id=proj_id, label=label)
            # Add a node to each project's graph
            node = GraphNode(
                id=f"node-{proj_id}",
                position=Position(x=0.0, y=0.0),
                data=graphNodeData(label=f"Node for {label}", simulation_id=""),
                type="simulation",
            )
            project.graph.add_node(node)
            created_projects.append(project)

        # List all projects
        projects_list = client.projects.list()
        assert len(projects_list) == 3

        # Each project should be a Project wrapper with graph access
        for project in projects_list:
            assert isinstance(project, ProjectManager)
            assert hasattr(project, "graph")

            # Each project's graph should have one node
            graph = project.graph.get()
            assert len(graph.nodes) == 1
            assert graph.nodes[0].id.startswith("node-")

    def test_user_friendly_api_demonstration(self, client):
        """Demonstrate the user-friendly API design."""
        # This test demonstrates the clean API we've achieved

        # 1. Create project - returns Project wrapper
        project = client.projects.create(project_id="api-demo", label="API Demo Project")

        # 2. Direct graph access - no project context needed
        assert project.graph.get().nodes == []  # Empty initially

        # 3. Add node - clean, intuitive
        node = GraphNode(
            id="demo-node",
            position=Position(x=100.0, y=100.0),
            data=graphNodeData(label="Demo Node", simulation_id=""),
            type="simulation",
        )
        project.graph.add_node(node)

        # 4. Immediate access to updated state
        assert len(project.graph.get().nodes) == 1

        # 5. All operations scoped to project automatically
        project.graph.update_node_position(node)
        project.graph.delete_node(node.id)

        # 6. Final state
        assert len(project.graph.get().nodes) == 0

        # This demonstrates the user-friendly design:
        # - project.graph.operation() instead of adapter.graph.operation(project, ...)
        # - Automatic project scoping
        # - Intuitive method names
        # - No manual context passing
