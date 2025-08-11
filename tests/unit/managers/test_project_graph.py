"""Unit tests for ProjectGraph manager - project-scoped graph operations."""

from unittest.mock import Mock

import pytest

from fluidize.managers.project_graph import ProjectGraph
from tests.fixtures.sample_graphs import SampleGraphs
from tests.fixtures.sample_projects import SampleProjects


class TestProjectGraph:
    """Test suite for ProjectGraph manager class."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend with graph handler."""
        backend = Mock()
        backend.graph = Mock()
        return backend

    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        return SampleProjects.standard_project()

    @pytest.fixture
    def project_graph(self, mock_backend, sample_project):
        """Create a ProjectGraph instance for testing."""
        return ProjectGraph(mock_backend, sample_project)

    def test_init_with_graph_initialization(self, mock_backend, sample_project):
        """Test ProjectGraph initialization triggers graph initialization."""
        mock_backend.graph.ensure_graph_initialized = Mock()

        project_graph = ProjectGraph(mock_backend, sample_project)

        assert project_graph.backend is mock_backend
        assert project_graph.project is sample_project
        mock_backend.graph.ensure_graph_initialized.assert_called_once_with(sample_project)

    def test_init_without_graph_handler(self, sample_project):
        """Test initialization when backend doesn't have graph handler."""
        backend_without_graph = Mock()
        del backend_without_graph.graph  # Remove graph attribute

        # Should not raise error
        project_graph = ProjectGraph(backend_without_graph, sample_project)

        assert project_graph.backend is backend_without_graph
        assert project_graph.project is sample_project

    def test_init_without_ensure_method(self, sample_project):
        """Test initialization when graph handler doesn't have ensure method."""
        backend = Mock()
        backend.graph = Mock()
        del backend.graph.ensure_graph_initialized  # Remove ensure method

        # Should not raise error
        project_graph = ProjectGraph(backend, sample_project)

        assert project_graph.backend is backend
        assert project_graph.project is sample_project

    def test_get_graph_success(self, project_graph, mock_backend):
        """Test successful graph retrieval."""
        expected_graph = SampleGraphs.complex_graph()
        mock_backend.graph.get_graph.return_value = expected_graph

        result = project_graph.get()

        assert result == expected_graph
        mock_backend.graph.get_graph.assert_called_once_with(project_graph.project)

    def test_get_empty_graph(self, project_graph, mock_backend):
        """Test retrieving empty graph."""
        empty_graph = SampleGraphs.empty_graph()
        mock_backend.graph.get_graph.return_value = empty_graph

        result = project_graph.get()

        assert result == empty_graph
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_add_node_success(self, project_graph, mock_backend):
        """Test successful node addition."""
        node = SampleGraphs.sample_nodes()[0]
        mock_backend.graph.insert_node.return_value = node

        result = project_graph.add_node(node)

        assert result == node
        mock_backend.graph.insert_node.assert_called_once_with(
            project_graph.project,
            node,
            True,  # Default sim_global=True
        )

    def test_add_node_with_sim_global_false(self, project_graph, mock_backend):
        """Test node addition with sim_global=False."""
        node = SampleGraphs.sample_nodes()[1]
        mock_backend.graph.insert_node.return_value = node

        result = project_graph.add_node(node, sim_global=False)

        assert result == node
        mock_backend.graph.insert_node.assert_called_once_with(project_graph.project, node, False)

    def test_update_node_position_success(self, project_graph, mock_backend):
        """Test successful node position update."""
        node = SampleGraphs.sample_nodes()[0]
        # Modify position for update test
        node.position.x = 500.0
        node.position.y = 600.0
        mock_backend.graph.update_node_position.return_value = node

        result = project_graph.update_node_position(node)

        assert result == node
        mock_backend.graph.update_node_position.assert_called_once_with(project_graph.project, node)

    def test_delete_node_success(self, project_graph, mock_backend):
        """Test successful node deletion."""
        node_id = "test-node-to-delete"

        project_graph.delete_node(node_id)

        mock_backend.graph.delete_node.assert_called_once_with(project_graph.project, node_id)

    def test_add_edge_success(self, project_graph, mock_backend):
        """Test successful edge addition."""
        edge = SampleGraphs.sample_edges()[0]
        mock_backend.graph.upsert_edge.return_value = edge

        result = project_graph.add_edge(edge)

        assert result == edge
        mock_backend.graph.upsert_edge.assert_called_once_with(project_graph.project, edge)

    def test_delete_edge_success(self, project_graph, mock_backend):
        """Test successful edge deletion."""
        edge_id = "test-edge-to-delete"

        project_graph.delete_edge(edge_id)

        mock_backend.graph.delete_edge.assert_called_once_with(project_graph.project, edge_id)

    def test_backend_error_propagation_get(self, project_graph, mock_backend):
        """Test that backend errors are propagated for get operations."""
        mock_backend.graph.get_graph.side_effect = FileNotFoundError("Graph file not found")

        with pytest.raises(FileNotFoundError, match="Graph file not found"):
            project_graph.get()

    def test_backend_error_propagation_add_node(self, project_graph, mock_backend):
        """Test that backend errors are propagated for add node operations."""
        node = SampleGraphs.sample_nodes()[0]
        mock_backend.graph.insert_node.side_effect = ValueError("Invalid node data")

        with pytest.raises(ValueError, match="Invalid node data"):
            project_graph.add_node(node)

    def test_backend_error_propagation_delete_node(self, project_graph, mock_backend):
        """Test that backend errors are propagated for delete node operations."""
        mock_backend.graph.delete_node.side_effect = FileNotFoundError("Node not found")

        with pytest.raises(FileNotFoundError, match="Node not found"):
            project_graph.delete_node("non-existent-node")

    def test_backend_error_propagation_add_edge(self, project_graph, mock_backend):
        """Test that backend errors are propagated for add edge operations."""
        edge = SampleGraphs.sample_edges()[0]
        mock_backend.graph.upsert_edge.side_effect = ValueError("Invalid edge")

        with pytest.raises(ValueError, match="Invalid edge"):
            project_graph.add_edge(edge)

    def test_project_scoping(self, mock_backend):
        """Test that different ProjectGraph instances are properly scoped to their projects."""
        project1 = SampleProjects.standard_project()
        project2 = SampleProjects.minimal_project()

        graph1 = ProjectGraph(mock_backend, project1)
        graph2 = ProjectGraph(mock_backend, project2)

        node = SampleGraphs.sample_nodes()[0]

        # Add node to first project graph
        graph1.add_node(node)

        # Add same node to second project graph
        graph2.add_node(node)

        # Verify each call was made with correct project context
        calls = mock_backend.graph.insert_node.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == project1  # First call with project1
        assert calls[1][0][0] == project2  # Second call with project2

    def test_all_methods_delegate_to_backend(self, project_graph, mock_backend):
        """Test that all ProjectGraph methods properly delegate to backend."""
        # Setup return values
        mock_graph_data = SampleGraphs.single_node_graph()
        mock_node = SampleGraphs.sample_nodes()[0]
        mock_edge = SampleGraphs.sample_edges()[0]

        mock_backend.graph.get_graph.return_value = mock_graph_data
        mock_backend.graph.insert_node.return_value = mock_node
        mock_backend.graph.update_node_position.return_value = mock_node
        mock_backend.graph.upsert_edge.return_value = mock_edge

        # Call all methods
        project_graph.get()
        project_graph.add_node(mock_node)
        project_graph.update_node_position(mock_node)
        project_graph.delete_node("test-id")
        project_graph.add_edge(mock_edge)
        project_graph.delete_edge("test-edge-id")

        # Verify all backend methods were called
        mock_backend.graph.get_graph.assert_called_once()
        mock_backend.graph.insert_node.assert_called_once()
        mock_backend.graph.update_node_position.assert_called_once()
        mock_backend.graph.delete_node.assert_called_once()
        mock_backend.graph.upsert_edge.assert_called_once()
        mock_backend.graph.delete_edge.assert_called_once()

    def test_project_context_consistency(self, project_graph, mock_backend):
        """Test that the same project context is used for all operations."""
        project = project_graph.project
        node = SampleGraphs.sample_nodes()[0]
        edge = SampleGraphs.sample_edges()[0]

        # Setup return values
        mock_backend.graph.get_graph.return_value = SampleGraphs.empty_graph()
        mock_backend.graph.insert_node.return_value = node
        mock_backend.graph.update_node_position.return_value = node
        mock_backend.graph.upsert_edge.return_value = edge

        # Perform various operations
        project_graph.get()
        project_graph.add_node(node)
        project_graph.update_node_position(node)
        project_graph.delete_node("test-id")
        project_graph.add_edge(edge)
        project_graph.delete_edge("test-edge-id")

        # Verify project context was passed consistently
        all_calls = [
            mock_backend.graph.get_graph.call_args_list,
            mock_backend.graph.insert_node.call_args_list,
            mock_backend.graph.update_node_position.call_args_list,
            mock_backend.graph.delete_node.call_args_list,
            mock_backend.graph.upsert_edge.call_args_list,
            mock_backend.graph.delete_edge.call_args_list,
        ]

        # All calls should include the same project as first argument
        for call_list in all_calls:
            if call_list:  # If method was called
                assert call_list[0][0][0] == project
