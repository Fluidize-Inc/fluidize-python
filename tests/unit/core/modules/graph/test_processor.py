"""Unit tests for GraphProcessor - core graph business logic."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fluidize.core.modules.graph.processor import GraphProcessor
from fluidize.core.types.graph import GraphData
from tests.fixtures.sample_graphs import SampleGraphs
from tests.fixtures.sample_projects import SampleProjects


class TestGraphProcessor:
    """Test suite for GraphProcessor class."""

    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        return SampleProjects.standard_project()

    @pytest.fixture
    def graph_processor(self, sample_project):
        """Create a GraphProcessor instance for testing."""
        return GraphProcessor(sample_project)

    @pytest.fixture
    def mock_path_finder(self):
        """Mock PathFinder for testing."""
        with patch("fluidize.core.modules.graph.processor.PathFinder") as mock_pf:
            yield mock_pf

    @pytest.fixture
    def mock_graph_model(self):
        """Mock Graph model for testing."""
        with patch("fluidize.core.modules.graph.processor.Graph") as mock_graph:
            yield mock_graph

    @pytest.fixture
    def mock_data_loader(self):
        """Mock DataLoader for testing."""
        with patch("fluidize.core.modules.graph.processor.DataLoader") as mock_dl:
            yield mock_dl

    def test_init(self, sample_project):
        """Test GraphProcessor initialization."""
        processor = GraphProcessor(sample_project)

        assert processor.project == sample_project

    def test_get_graph_success(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test successful graph retrieval."""
        # Setup mocks
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        expected_graph_data = SampleGraphs.complex_graph()
        mock_graph_instance.to_graph_data.return_value = expected_graph_data
        mock_graph_model.from_file.return_value = mock_graph_instance

        result = graph_processor.get_graph()

        assert result == expected_graph_data
        mock_path_finder.get_project_path.assert_called_once_with(sample_project)
        mock_graph_model.from_file.assert_called_once_with(mock_graph_path)
        mock_graph_instance.heal.assert_called_once()
        mock_graph_instance.to_graph_data.assert_called_once()

    def test_get_graph_file_error(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test get_graph when file operation fails."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_model.from_file.side_effect = Exception("File error")

        result = graph_processor.get_graph()

        # Should return empty graph on error
        assert isinstance(result, GraphData)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_insert_node_success(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test successful node insertion."""
        # Setup mocks
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]

        result = graph_processor.insert_node(node, True)

        assert result == node
        mock_graph_model.from_file.assert_called_once_with(mock_graph_path)
        mock_graph_instance.add_node.assert_called_once_with(node)
        mock_graph_instance.save_to_file.assert_called_once_with(mock_graph_path)

    def test_insert_node_with_simulation_copy(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node insertion with simulation template copying."""
        # Setup mocks
        mock_project_path = Path("/test/project")
        mock_simulation_path = Path("/test/simulation")
        mock_node_path = Path("/test/project/node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Create node with simulation_id
        node = SampleGraphs.sample_nodes()[0]
        # Add simulation_id to node data
        node.data.simulation_id = "test-sim-123"

        result = graph_processor.insert_node(node, True)

        assert result == node
        mock_path_finder.get_simulation_path.assert_called_once_with(simulation_id="test-sim-123", sim_global=True)
        mock_path_finder.get_node_path.assert_called_once_with(sample_project, node.id)
        mock_data_loader.copy_directory.assert_called_once_with(source=mock_simulation_path, destination=mock_node_path)

    def test_insert_node_simulation_copy_failure(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node insertion when simulation copy fails."""
        # Setup mocks
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Make simulation copy fail
        mock_data_loader.copy_directory.side_effect = Exception("Copy failed")

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = "test-sim-123"

        # Should not raise exception, just continue
        result = graph_processor.insert_node(node, True)

        assert result == node
        # Graph operations should still succeed
        mock_graph_instance.add_node.assert_called_once_with(node)
        mock_graph_instance.save_to_file.assert_called_once()

    def test_insert_node_without_simulation_id(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node insertion without simulation_id creates empty node directory."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        # Ensure no simulation_id
        node.data.simulation_id = ""

        # Mock the _initialize_node_directory method
        with patch.object(graph_processor, "_initialize_node_directory") as mock_init:
            result = graph_processor.insert_node(node, True)

            assert result == node
            # Should not attempt to copy simulation
            mock_data_loader.copy_directory.assert_not_called()
            # Should initialize empty node directory
            mock_init.assert_called_once_with(node.id)

    def test_insert_node_invalid_simulation_id(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node insertion with invalid simulation_id throws error."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Setup simulation path finder
        mock_simulation_path = Path("/test/nonexistent-simulation")
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path

        # Mock that the simulation metadata file doesn't exist
        mock_data_loader.check_file_exists.return_value = False

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = "nonexistent-simulation"

        # Should raise ValueError for invalid simulation
        with pytest.raises(ValueError, match="Simulation 'nonexistent-simulation' not found"):
            graph_processor.insert_node(node, True)

        # Graph should still be updated (but node directory not created)
        mock_graph_instance.add_node.assert_called_once_with(node)
        mock_graph_instance.save_to_file.assert_called_once()
        # Should not attempt to copy nonexistent simulation
        mock_data_loader.copy_directory.assert_not_called()

    def test_initialize_node_directory(self, graph_processor, mock_path_finder, sample_project):
        """Test _initialize_node_directory creates node directory with default files."""
        from unittest.mock import patch

        mock_node_path = Path("/test/project/test-node")
        mock_path_finder.get_node_path.return_value = mock_node_path

        with patch("fluidize.core.modules.graph.processor.DataWriter") as mock_data_writer:
            graph_processor._initialize_node_directory("test-node")

            # Should create directory
            mock_data_writer.create_directory.assert_called_once_with(mock_node_path)

            # Should create parameters.json
            expected_params = {"metadata": {}, "parameters": {}}
            params_path = mock_node_path / "parameters.json"
            mock_data_writer.write_json.assert_called_with(params_path, expected_params)

            # Should create properties.yaml
            expected_properties = {"properties": {}}
            properties_path = mock_node_path / "properties.yaml"
            mock_data_writer.write_yaml.assert_called_with(properties_path, expected_properties)

            # Verify get_node_path was called with correct parameters
            mock_path_finder.get_node_path.assert_called_once_with(sample_project, "test-node")

    def test_update_node_position_success(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test successful node position update."""
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        node.position.x = 500.0
        node.position.y = 600.0

        result = graph_processor.update_node_position(node)

        assert result == node
        mock_graph_instance.add_node.assert_called_once_with(node)  # add_node also updates
        mock_graph_instance.save_to_file.assert_called_once_with(mock_graph_path)

    def test_delete_node_success(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test successful node deletion."""
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_node_path = Path("/test/project/node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node_id = "test-node-id"

        graph_processor.delete_node(node_id)

        mock_graph_instance.remove_node.assert_called_once_with(node_id)
        mock_graph_instance.save_to_file.assert_called_once_with(mock_graph_path)
        mock_path_finder.get_node_path.assert_called_once_with(sample_project, node_id)
        mock_data_loader.remove_directory.assert_called_once_with(mock_node_path)

    def test_delete_node_directory_removal_failure(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node deletion when directory removal fails."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Make directory removal fail
        mock_data_loader.remove_directory.side_effect = Exception("Remove failed")

        node_id = "test-node-id"

        # Should not raise exception
        graph_processor.delete_node(node_id)

        # Graph operations should still succeed
        mock_graph_instance.remove_node.assert_called_once_with(node_id)
        mock_graph_instance.save_to_file.assert_called_once()

    def test_upsert_edge_success(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test successful edge upsert."""
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        edge = SampleGraphs.sample_edges()[0]

        result = graph_processor.upsert_edge(edge)

        assert result == edge
        mock_graph_instance.add_edge.assert_called_once_with(edge)
        mock_graph_instance.save_to_file.assert_called_once_with(mock_graph_path)

    def test_delete_edge_success(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test successful edge deletion."""
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        edge_id = "test-edge-id"

        graph_processor.delete_edge(edge_id)

        mock_graph_instance.remove_edge.assert_called_once_with(edge_id)
        mock_graph_instance.save_to_file.assert_called_once_with(mock_graph_path)

    def test_ensure_graph_file_exists_creates_file(
        self, graph_processor, mock_path_finder, mock_graph_model, sample_project
    ):
        """Test that ensure_graph_file_exists creates file when it doesn't exist."""
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_path_finder.get_project_path.return_value = mock_project_path

        # Mock the path exists method using string path
        with patch("pathlib.Path.exists", return_value=False):
            mock_empty_graph = Mock()
            mock_graph_model.return_value = mock_empty_graph

            graph_processor._ensure_graph_file_exists()

            mock_graph_model.assert_called_once()  # Empty graph created
            mock_empty_graph.save_to_file.assert_called_once_with(mock_graph_path)

    def test_ensure_graph_file_exists_file_already_exists(
        self, graph_processor, mock_path_finder, mock_graph_model, sample_project
    ):
        """Test that ensure_graph_file_exists does nothing when file exists."""
        mock_project_path = Path("/test/project")
        mock_path_finder.get_project_path.return_value = mock_project_path

        # Mock path exists
        with patch("pathlib.Path.exists", return_value=True):
            graph_processor._ensure_graph_file_exists()

            # Should not create new graph
            mock_graph_model.assert_not_called()

    def test_multiple_operations_sequence(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test sequence of multiple operations."""
        mock_project_path = Path("/test/project")
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance
        mock_graph_instance.to_graph_data.return_value = SampleGraphs.empty_graph()

        node = SampleGraphs.sample_nodes()[0]
        edge = SampleGraphs.sample_edges()[0]

        # Perform sequence of operations
        graph_data = graph_processor.get_graph()
        inserted_node = graph_processor.insert_node(node)
        updated_node = graph_processor.update_node_position(node)
        upserted_edge = graph_processor.upsert_edge(edge)
        graph_processor.delete_edge(edge.id)
        graph_processor.delete_node(node.id)

        # Verify all operations were performed
        assert graph_data is not None
        assert inserted_node == node
        assert updated_node == node
        assert upserted_edge == edge

        # Verify graph was loaded multiple times (once per operation)
        # get_graph, insert_node, update_node_position, upsert_edge, delete_edge, delete_node = 6 operations
        assert mock_graph_model.from_file.call_count == 6

    def test_path_finder_usage_consistency(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test that PathFinder is used consistently across operations."""
        mock_project_path = Path("/test/project")
        mock_path_finder.get_project_path.return_value = mock_project_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance
        mock_graph_instance.to_graph_data.return_value = SampleGraphs.empty_graph()

        node = SampleGraphs.sample_nodes()[0]
        edge = SampleGraphs.sample_edges()[0]

        # Perform various operations
        graph_processor.get_graph()
        graph_processor.insert_node(node)
        graph_processor.update_node_position(node)
        graph_processor.upsert_edge(edge)
        graph_processor.delete_edge(edge.id)
        graph_processor.delete_node(node.id)

        # PathFinder should be called consistently with the same project
        for call_args in mock_path_finder.get_project_path.call_args_list:
            assert call_args[0][0] == sample_project

    def test_error_handling_propagation(self, graph_processor, mock_path_finder, mock_graph_model, sample_project):
        """Test that errors from dependencies are properly handled."""
        mock_path_finder.get_project_path.side_effect = Exception("PathFinder error")

        # get_graph handles errors gracefully and returns empty graph
        result = graph_processor.get_graph()
        assert isinstance(result, GraphData)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    @pytest.mark.parametrize("sim_global", [True, False])
    def test_insert_node_sim_global_parameter(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project, sim_global
    ):
        """Test insert_node with different sim_global values."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = "test-sim"

        graph_processor.insert_node(node, sim_global)

        if hasattr(node.data, "simulation_id") and node.data.simulation_id:
            mock_path_finder.get_simulation_path.assert_called_once_with(
                simulation_id="test-sim", sim_global=sim_global
            )

    def test_processor_project_isolation(self, mock_path_finder, mock_graph_model):
        """Test that different processors for different projects are isolated."""
        project1 = SampleProjects.standard_project()
        project2 = SampleProjects.minimal_project()

        processor1 = GraphProcessor(project1)
        processor2 = GraphProcessor(project2)

        mock_path_finder.get_project_path.return_value = Path("/test")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance
        mock_graph_instance.to_graph_data.return_value = SampleGraphs.empty_graph()

        processor1.get_graph()
        processor2.get_graph()

        # Verify each processor was called with its respective project
        call_args_list = mock_path_finder.get_project_path.call_args_list
        assert len(call_args_list) == 2
        assert call_args_list[0][0][0] == project1
        assert call_args_list[1][0][0] == project2
