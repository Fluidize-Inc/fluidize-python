"""Unit tests for GraphHandler - local backend graph interface."""

from unittest.mock import Mock, patch

import pytest

from fluidize.backends.local.graph import GraphHandler
from fluidize.core.types.graph import GraphData
from tests.fixtures.sample_graphs import SampleGraphs
from tests.fixtures.sample_projects import SampleProjects


class TestGraphHandler:
    """Test suite for GraphHandler class."""

    @pytest.fixture
    def mock_processor(self):
        """Create a mock GraphProcessor for testing."""
        with patch("fluidize.backends.local.graph.GraphProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            yield mock_processor

    @pytest.fixture
    def graph_handler(self, mock_processor):
        """Create a GraphHandler instance for testing."""
        return GraphHandler()

    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        return SampleProjects.standard_project()

    def test_init(self):
        """Test GraphHandler initialization."""
        handler = GraphHandler()
        # GraphHandler has minimal initialization
        assert handler is not None

    def test_get_graph_success(self, graph_handler, mock_processor, sample_project):
        """Test successful graph retrieval."""
        expected_graph = SampleGraphs.complex_graph()
        mock_processor.get_graph.return_value = expected_graph

        result = graph_handler.get_graph(sample_project)

        assert result == expected_graph
        mock_processor.get_graph.assert_called_once()

    def test_get_graph_empty(self, graph_handler, mock_processor, sample_project):
        """Test retrieving empty graph."""
        empty_graph = SampleGraphs.empty_graph()
        mock_processor.get_graph.return_value = empty_graph

        result = graph_handler.get_graph(sample_project)

        assert result == empty_graph
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_get_graph_processor_creation(self, sample_project):
        """Test that GraphProcessor is created with correct project."""
        with patch("fluidize.backends.local.graph.GraphProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.get_graph.return_value = SampleGraphs.empty_graph()

            handler = GraphHandler()
            handler.get_graph(sample_project)

            # Verify GraphProcessor was created with the project
            mock_processor_class.assert_called_once_with(sample_project)

    def test_insert_node_success(self, graph_handler, mock_processor, sample_project):
        """Test successful node insertion."""
        node = SampleGraphs.sample_nodes()[0]
        mock_processor.insert_node.return_value = node

        result = graph_handler.insert_node(sample_project, node, True)

        assert result == node
        mock_processor.insert_node.assert_called_once_with(node, True)

    def test_insert_node_with_sim_global_false(self, graph_handler, mock_processor, sample_project):
        """Test node insertion with sim_global=False."""
        node = SampleGraphs.sample_nodes()[1]
        mock_processor.insert_node.return_value = node

        result = graph_handler.insert_node(sample_project, node, False)

        assert result == node
        mock_processor.insert_node.assert_called_once_with(node, False)

    def test_insert_node_default_sim_global(self, graph_handler, mock_processor, sample_project):
        """Test node insertion with default sim_global value."""
        node = SampleGraphs.sample_nodes()[0]
        mock_processor.insert_node.return_value = node

        result = graph_handler.insert_node(sample_project, node)

        assert result == node
        mock_processor.insert_node.assert_called_once_with(node, True)  # Default is True

    def test_update_node_position_success(self, graph_handler, mock_processor, sample_project):
        """Test successful node position update."""
        node = SampleGraphs.sample_nodes()[0]
        # Modify position for update
        node.position.x = 500.0
        node.position.y = 600.0
        mock_processor.update_node_position.return_value = node

        result = graph_handler.update_node_position(sample_project, node)

        assert result == node
        mock_processor.update_node_position.assert_called_once_with(node)

    def test_delete_node_success(self, graph_handler, mock_processor, sample_project):
        """Test successful node deletion."""
        node_id = "test-node-to-delete"

        graph_handler.delete_node(sample_project, node_id)

        mock_processor.delete_node.assert_called_once_with(node_id)

    def test_upsert_edge_success(self, graph_handler, mock_processor, sample_project):
        """Test successful edge upsert."""
        edge = SampleGraphs.sample_edges()[0]
        mock_processor.upsert_edge.return_value = edge

        result = graph_handler.upsert_edge(sample_project, edge)

        assert result == edge
        mock_processor.upsert_edge.assert_called_once_with(edge)

    def test_delete_edge_success(self, graph_handler, mock_processor, sample_project):
        """Test successful edge deletion."""
        edge_id = "test-edge-to-delete"

        graph_handler.delete_edge(sample_project, edge_id)

        mock_processor.delete_edge.assert_called_once_with(edge_id)

    def test_ensure_graph_initialized(self, graph_handler, mock_processor, sample_project):
        """Test graph initialization."""
        graph_handler.ensure_graph_initialized(sample_project)

        mock_processor._ensure_graph_file_exists.assert_called_once()

    def test_processor_error_propagation_get_graph(self, graph_handler, mock_processor, sample_project):
        """Test that processor errors are propagated for get_graph."""
        mock_processor.get_graph.side_effect = FileNotFoundError("Graph file not found")

        with pytest.raises(FileNotFoundError, match="Graph file not found"):
            graph_handler.get_graph(sample_project)

    def test_processor_error_propagation_insert_node(self, graph_handler, mock_processor, sample_project):
        """Test that processor errors are propagated for insert_node."""
        node = SampleGraphs.sample_nodes()[0]
        mock_processor.insert_node.side_effect = ValueError("Invalid node data")

        with pytest.raises(ValueError, match="Invalid node data"):
            graph_handler.insert_node(sample_project, node)

    def test_processor_error_propagation_delete_node(self, graph_handler, mock_processor, sample_project):
        """Test that processor errors are propagated for delete_node."""
        mock_processor.delete_node.side_effect = FileNotFoundError("Node not found")

        with pytest.raises(FileNotFoundError, match="Node not found"):
            graph_handler.delete_node(sample_project, "non-existent")

    def test_processor_error_propagation_upsert_edge(self, graph_handler, mock_processor, sample_project):
        """Test that processor errors are propagated for upsert_edge."""
        edge = SampleGraphs.sample_edges()[0]
        mock_processor.upsert_edge.side_effect = ValueError("Invalid edge data")

        with pytest.raises(ValueError, match="Invalid edge data"):
            graph_handler.upsert_edge(sample_project, edge)

    def test_processor_error_propagation_delete_edge(self, graph_handler, mock_processor, sample_project):
        """Test that processor errors are propagated for delete_edge."""
        mock_processor.delete_edge.side_effect = FileNotFoundError("Edge not found")

        with pytest.raises(FileNotFoundError, match="Edge not found"):
            graph_handler.delete_edge(sample_project, "non-existent-edge")

    def test_processor_creation_per_operation(self, sample_project):
        """Test that a new GraphProcessor is created for each operation."""
        with patch("fluidize.backends.local.graph.GraphProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.get_graph.return_value = SampleGraphs.empty_graph()
            mock_processor.insert_node.return_value = SampleGraphs.sample_nodes()[0]

            handler = GraphHandler()

            # Perform multiple operations
            handler.get_graph(sample_project)
            handler.insert_node(sample_project, SampleGraphs.sample_nodes()[0])
            handler.delete_node(sample_project, "test-id")

            # Verify processor was created for each operation
            assert mock_processor_class.call_count == 3
            # Each call should be with the same project
            for call_args in mock_processor_class.call_args_list:
                assert call_args[0][0] == sample_project

    def test_multiple_projects_isolation(self):
        """Test that operations on different projects are isolated."""
        project1 = SampleProjects.standard_project()
        project2 = SampleProjects.minimal_project()

        with patch("fluidize.backends.local.graph.GraphProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.get_graph.return_value = SampleGraphs.empty_graph()

            handler = GraphHandler()

            # Perform operations on different projects
            handler.get_graph(project1)
            handler.get_graph(project2)

            # Verify separate processors were created for each project
            assert mock_processor_class.call_count == 2
            call_args_list = mock_processor_class.call_args_list
            assert call_args_list[0][0][0] == project1
            assert call_args_list[1][0][0] == project2

    def test_all_crud_operations_flow(self, sample_project):
        """Test complete CRUD flow for graph operations."""
        with patch("fluidize.backends.local.graph.GraphProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor

            # Setup return values
            mock_processor.get_graph.return_value = SampleGraphs.single_node_graph()
            mock_processor.insert_node.return_value = SampleGraphs.sample_nodes()[0]
            mock_processor.update_node_position.return_value = SampleGraphs.sample_nodes()[0]
            mock_processor.upsert_edge.return_value = SampleGraphs.sample_edges()[0]

            handler = GraphHandler()
            node = SampleGraphs.sample_nodes()[0]
            edge = SampleGraphs.sample_edges()[0]

            # Perform full CRUD cycle
            graph_data = handler.get_graph(sample_project)
            inserted_node = handler.insert_node(sample_project, node)
            updated_node = handler.update_node_position(sample_project, node)
            handler.delete_node(sample_project, "test-node-id")
            upserted_edge = handler.upsert_edge(sample_project, edge)
            handler.delete_edge(sample_project, "test-edge-id")
            handler.ensure_graph_initialized(sample_project)

            # Verify all operations were called on processor
            mock_processor.get_graph.assert_called_once()
            mock_processor.insert_node.assert_called_once_with(node, True)
            mock_processor.update_node_position.assert_called_once_with(node)
            mock_processor.delete_node.assert_called_once_with("test-node-id")
            mock_processor.upsert_edge.assert_called_once_with(edge)
            mock_processor.delete_edge.assert_called_once_with("test-edge-id")
            mock_processor._ensure_graph_file_exists.assert_called_once()

            # Verify return values
            assert isinstance(graph_data, GraphData)
            assert inserted_node == node
            assert updated_node == node
            assert upserted_edge == edge

    @pytest.mark.parametrize(
        "operation,method_name,args",
        [
            ("get_graph", "get_graph", []),
            ("insert_node", "insert_node", [SampleGraphs.sample_nodes()[0], True]),
            ("update_node_position", "update_node_position", [SampleGraphs.sample_nodes()[0]]),
            ("delete_node", "delete_node", ["test-node-id"]),
            ("upsert_edge", "upsert_edge", [SampleGraphs.sample_edges()[0]]),
            ("delete_edge", "delete_edge", ["test-edge-id"]),
            ("ensure_graph_initialized", "_ensure_graph_file_exists", []),
        ],
    )
    def test_individual_operations(self, sample_project, operation, method_name, args):
        """Test each graph operation individually."""
        with patch("fluidize.backends.local.graph.GraphProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor

            # Setup default return values
            mock_processor.get_graph.return_value = SampleGraphs.empty_graph()
            mock_processor.insert_node.return_value = SampleGraphs.sample_nodes()[0]
            mock_processor.update_node_position.return_value = SampleGraphs.sample_nodes()[0]
            mock_processor.upsert_edge.return_value = SampleGraphs.sample_edges()[0]

            handler = GraphHandler()

            # Call the operation
            handler_method = getattr(handler, operation)
            if operation == "ensure_graph_initialized":
                handler_method(sample_project)
            else:
                handler_method(sample_project, *args)

            # Verify processor was created with project
            mock_processor_class.assert_called_once_with(sample_project)

            # Verify correct processor method was called
            processor_method = getattr(mock_processor, method_name)
            if args:
                processor_method.assert_called_once_with(*args)
            else:
                processor_method.assert_called_once()
