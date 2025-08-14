"""Unit tests for GraphProcessor - core graph business logic."""

import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fluidize.core.modules.graph.processor import GraphProcessor
from fluidize.core.types.graph import GraphData
from fluidize.core.types.node import author, nodeMetadata_simulation, nodeProperties_simulation, tag
from fluidize.core.types.runs import RunStatus
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
        mock_metadata_path = mock_simulation_path / "metadata.yaml"

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Mock that simulation metadata file exists (valid simulation)
        mock_data_loader.check_file_exists.return_value = True

        # Create node with simulation_id
        node = SampleGraphs.sample_nodes()[0]
        # Add simulation_id to node data
        node.data.simulation_id = "test-sim-123"

        result = graph_processor.insert_node(node, True)

        assert result == node
        mock_path_finder.get_simulation_path.assert_called_once_with(simulation_id="test-sim-123", sim_global=True)
        mock_path_finder.get_node_path.assert_called_once_with(sample_project, node.id)
        mock_data_loader.check_file_exists.assert_called_once_with(mock_metadata_path)
        mock_data_loader.copy_directory.assert_called_once_with(source=mock_simulation_path, destination=mock_node_path)

    def test_insert_node_simulation_copy_failure(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node insertion when simulation copy fails - should raise ValueError."""
        # Setup mocks
        mock_project_path = Path("/test/project")
        mock_simulation_path = Path("/test/simulation")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Mock that simulation metadata file exists (so it passes validation)
        mock_data_loader.check_file_exists.return_value = True
        # But make simulation copy fail
        mock_data_loader.copy_directory.side_effect = Exception("Copy failed")

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = "test-sim-123"

        # Should raise ValueError when copy fails (fail fast behavior)
        with pytest.raises(ValueError):
            graph_processor.insert_node(node, True)

        # Graph operations should still have been attempted
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
        mock_project_path = Path("/test/project")
        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Setup simulation path finder
        mock_simulation_path = Path("/test/nonexistent-simulation")
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path

        # Mock that the simulation metadata file doesn't exist
        mock_metadata_path = mock_simulation_path / "metadata.yaml"
        mock_data_loader.check_file_exists.return_value = False

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = "nonexistent-simulation"

        # Should raise ValueError for invalid simulation (gets re-raised as generic ValueError)
        with pytest.raises(ValueError):
            graph_processor.insert_node(node, True)

        # Graph should still be updated (but node directory not created)
        mock_graph_instance.add_node.assert_called_once_with(node)
        mock_graph_instance.save_to_file.assert_called_once()
        # Should check for metadata file existence
        mock_data_loader.check_file_exists.assert_called_once_with(mock_metadata_path)
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

            # Should create parameters.json with correct structure
            expected_params = {"metadata": {}, "parameters": {}}
            params_path = mock_node_path / "parameters.json"
            mock_data_writer.write_json.assert_called_with(params_path, expected_params)

            # Should create properties.yaml with correct structure
            expected_properties = {"properties": {}}
            properties_path = mock_node_path / "properties.yaml"
            mock_data_writer.write_yaml.assert_called_with(properties_path, expected_properties)

            # Verify get_node_path was called with correct parameters
            mock_path_finder.get_node_path.assert_called_once_with(sample_project, "test-node")

            # Verify both file writes were called
            assert mock_data_writer.write_json.call_count == 1
            assert mock_data_writer.write_yaml.call_count == 1

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
        mock_node_path = Path("/test/project/test-node-basic")
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance
        mock_graph_instance.to_graph_data.return_value = SampleGraphs.empty_graph()

        node = SampleGraphs.sample_nodes()[0]
        # Remove simulation_id to avoid simulation path lookup that would cause issues
        node.data.simulation_id = ""
        edge = SampleGraphs.sample_edges()[0]

        # Mock the _initialize_node_directory method to avoid DataWriter dependencies
        with (
            patch.object(graph_processor, "_initialize_node_directory"),
            patch("fluidize.core.modules.graph.processor.DataLoader"),
        ):
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

    def test_insert_node_without_simulation_id_none(
        self, graph_processor, mock_path_finder, mock_graph_model, sample_project
    ):
        """Test node insertion when simulation_id is None."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = None  # Explicitly None

        with patch.object(graph_processor, "_initialize_node_directory") as mock_init:
            result = graph_processor.insert_node(node, True)

            assert result == node
            mock_init.assert_called_once_with(node.id)
            mock_graph_instance.add_node.assert_called_once_with(node)
            mock_graph_instance.save_to_file.assert_called_once()

    def test_insert_node_without_simulation_id_missing_attribute(
        self, graph_processor, mock_path_finder, mock_graph_model, sample_project
    ):
        """Test node insertion when simulation_id attribute doesn't exist."""
        mock_path_finder.get_project_path.return_value = Path("/test/project")
        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        # Remove the simulation_id attribute entirely
        delattr(node.data, "simulation_id")

        with patch.object(graph_processor, "_initialize_node_directory") as mock_init:
            result = graph_processor.insert_node(node, True)

            assert result == node
            mock_init.assert_called_once_with(node.id)
            mock_graph_instance.add_node.assert_called_once_with(node)
            mock_graph_instance.save_to_file.assert_called_once()

    def test_insert_node_with_whitespace_only_simulation_id(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test node insertion when simulation_id contains only whitespace - treated as valid simulation_id."""
        mock_project_path = Path("/test/project")
        mock_simulation_path = Path("/test/simulation")
        mock_node_path = Path("/test/project/node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Current implementation treats whitespace-only as valid simulation_id and tries to find it
        # Mock that the simulation doesn't exist (which it won't for whitespace)
        mock_data_loader.check_file_exists.return_value = False

        node = SampleGraphs.sample_nodes()[0]
        node.data.simulation_id = "   "  # Whitespace only - current code treats as truthy

        # Should raise ValueError because whitespace simulation won't exist
        with pytest.raises(ValueError):
            graph_processor.insert_node(node, True)

    def test_initialize_node_directory_error_handling(self, graph_processor, mock_path_finder, sample_project):
        """Test _initialize_node_directory error handling when directory creation fails."""
        from unittest.mock import patch

        mock_node_path = Path("/test/project/test-node")
        mock_path_finder.get_node_path.return_value = mock_node_path

        with patch("fluidize.core.modules.graph.processor.DataWriter") as mock_data_writer:
            # Make directory creation fail
            mock_data_writer.create_directory.side_effect = Exception("Permission denied")

            # Should propagate the exception
            with pytest.raises(Exception, match="Permission denied"):
                graph_processor._initialize_node_directory("test-node")

    def test_initialize_node_directory_file_creation_error(self, graph_processor, mock_path_finder, sample_project):
        """Test _initialize_node_directory when file creation fails."""
        from unittest.mock import patch

        mock_node_path = Path("/test/project/test-node")
        mock_path_finder.get_node_path.return_value = mock_node_path

        with patch("fluidize.core.modules.graph.processor.DataWriter") as mock_data_writer:
            # Directory creation succeeds, but JSON file creation fails
            mock_data_writer.write_json.side_effect = Exception("Write failed")

            # Should propagate the exception
            with pytest.raises(Exception, match="Write failed"):
                graph_processor._initialize_node_directory("test-node")

            # Directory should still have been created
            mock_data_writer.create_directory.assert_called_once_with(mock_node_path)

    def test_insert_node_filesystem_consistency_valid_sim(
        self, graph_processor, mock_path_finder, mock_graph_model, mock_data_loader, sample_project
    ):
        """Test that inserting a node with valid simulation_id creates filesystem structure."""
        mock_project_path = Path("/test/project")
        mock_simulation_path = Path("/test/simulation")
        mock_node_path = Path("/test/project/node-123")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_simulation_path.return_value = mock_simulation_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        # Mock successful simulation validation and copy
        mock_data_loader.check_file_exists.return_value = True

        node = SampleGraphs.sample_nodes()[0]
        node.id = "node-123"
        node.data.simulation_id = "valid-sim"

        result = graph_processor.insert_node(node, True)

        # Verify graph operations
        assert result == node
        mock_graph_instance.add_node.assert_called_once_with(node)
        mock_graph_instance.save_to_file.assert_called_once()

        # Verify filesystem operations
        mock_path_finder.get_node_path.assert_called_once_with(sample_project, "node-123")
        mock_data_loader.copy_directory.assert_called_once_with(source=mock_simulation_path, destination=mock_node_path)

    def test_insert_node_filesystem_consistency_no_sim(
        self, graph_processor, mock_path_finder, mock_graph_model, sample_project
    ):
        """Test that inserting a node without simulation_id creates basic filesystem structure."""
        mock_project_path = Path("/test/project")
        mock_node_path = Path("/test/project/node-456")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        node.id = "node-456"
        node.data.simulation_id = ""  # No simulation

        with patch("fluidize.core.modules.graph.processor.DataWriter") as mock_data_writer:
            result = graph_processor.insert_node(node, True)

            # Verify graph operations
            assert result == node
            mock_graph_instance.add_node.assert_called_once_with(node)
            mock_graph_instance.save_to_file.assert_called_once()

            # Verify filesystem operations - should create basic structure
            # get_node_path is called twice: once in insert_node and once in _initialize_node_directory
            assert mock_path_finder.get_node_path.call_count == 2
            mock_path_finder.get_node_path.assert_called_with(sample_project, "node-456")
            mock_data_writer.create_directory.assert_called_once_with(mock_node_path)

            # Should create both default files
            expected_params = {"metadata": {}, "parameters": {}}
            expected_properties = {"properties": {}}
            params_path = mock_node_path / "parameters.json"
            properties_path = mock_node_path / "properties.yaml"

            mock_data_writer.write_json.assert_called_once_with(params_path, expected_params)
            mock_data_writer.write_yaml.assert_called_once_with(properties_path, expected_properties)

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

    # Sample data for insert_node_from_scratch tests
    @pytest.fixture
    def sample_node_properties(self):
        """Sample nodeProperties_simulation for testing."""
        return nodeProperties_simulation(
            container_image="test/container:latest",
            image_name="test-image",
            simulation_mount_path="/app/simulation",
            source_output_folder="output",
            should_run=True,
            last_run=None,
            run_status=RunStatus.NOT_RUN,
            version="1.0",
        )

    @pytest.fixture
    def sample_node_metadata(self):
        """Sample nodeMetadata_simulation for testing."""
        return nodeMetadata_simulation(
            name="Test Simulation",
            id="test-sim-123",
            description="A test simulation for unit testing",
            date=datetime.date(2024, 1, 15),
            version="1.0.0",
            authors=[author(name="Test Author", institution="Test University", email="test@example.com")],
            tags=[tag(name="test", description="Test tag", color="#FF0000")],
            code_url="https://github.com/test/repo",
            paper_url="https://example.com/paper",
            mlflow_run_id=None,
        )

    @pytest.fixture
    def minimal_node_properties(self):
        """Minimal nodeProperties_simulation with only required fields."""
        return nodeProperties_simulation(container_image="minimal/container:latest", simulation_mount_path="/app")

    @pytest.fixture
    def minimal_node_metadata(self):
        """Minimal nodeMetadata_simulation with only required fields."""
        return nodeMetadata_simulation(
            name="Minimal Test",
            id="minimal-sim",
            description="Minimal test simulation",
            date=None,
            version="1.0",
            authors=[author(name="Minimal Author", institution="Test")],
            tags=[],
            code_url=None,
            paper_url=None,
        )

    def test_insert_node_from_scratch_success(
        self,
        graph_processor,
        mock_path_finder,
        mock_graph_model,
        sample_project,
        sample_node_properties,
        sample_node_metadata,
    ):
        """Test successful node insertion from scratch."""
        # Setup mocks
        mock_project_path = Path("/test/project")
        mock_graph_path = mock_project_path / "graph.json"
        mock_node_path = Path("/test/project/test-node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]

        with patch.object(graph_processor, "_create_node_from_scratch") as mock_create:
            result = graph_processor.insert_node_from_scratch(node, sample_node_properties, sample_node_metadata, None)

            assert result == node
            mock_graph_model.from_file.assert_called_once_with(mock_graph_path)
            mock_graph_instance.add_node.assert_called_once_with(node)
            mock_graph_instance.save_to_file.assert_called_once_with(mock_graph_path)
            mock_create.assert_called_once_with(mock_node_path, sample_node_properties, sample_node_metadata, None)

    def test_insert_node_from_scratch_with_repo_link(
        self,
        graph_processor,
        mock_path_finder,
        mock_graph_model,
        sample_project,
        sample_node_properties,
        sample_node_metadata,
    ):
        """Test node insertion from scratch with repository link."""
        mock_project_path = Path("/test/project")
        mock_node_path = Path("/test/project/test-node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        repo_link = "https://github.com/test/repo.git"

        with patch.object(graph_processor, "_create_node_from_scratch") as mock_create:
            result = graph_processor.insert_node_from_scratch(
                node, sample_node_properties, sample_node_metadata, repo_link
            )

            assert result == node
            mock_create.assert_called_once_with(mock_node_path, sample_node_properties, sample_node_metadata, repo_link)

    def test_insert_node_from_scratch_creation_failure_cleanup(
        self,
        graph_processor,
        mock_path_finder,
        mock_graph_model,
        mock_data_loader,
        sample_project,
        sample_node_properties,
        sample_node_metadata,
    ):
        """Test cleanup when node creation fails."""
        mock_project_path = Path("/test/project")
        mock_node_path = Path("/test/project/test-node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]

        with patch.object(graph_processor, "_create_node_from_scratch") as mock_create:
            mock_create.side_effect = Exception("Creation failed")

            with pytest.raises(ValueError, match="Failed to create node from scratch"):
                graph_processor.insert_node_from_scratch(node, sample_node_properties, sample_node_metadata, None)

            # Verify cleanup was attempted
            mock_data_loader.remove_directory.assert_called_once_with(mock_node_path)

    def test_create_node_from_scratch_success(self, graph_processor, sample_node_properties, sample_node_metadata):
        """Test _create_node_from_scratch creates all necessary files and directories."""
        mock_node_path = Path("/test/project/test-node")

        with (
            patch("fluidize.core.modules.graph.processor.DataWriter") as mock_data_writer,
            patch.object(graph_processor, "_validate_and_warn_missing_fields") as mock_validate,
            patch.object(graph_processor, "_clone_repository") as mock_clone,
            # Mock the DataLoader and DataWriter used inside the save() method
            patch("fluidize.core.utils.dataloader.data_loader.DataLoader") as mock_data_loader,
            patch("fluidize.core.utils.dataloader.data_writer.DataWriter") as mock_save_data_writer,
        ):
            # Mock DataLoader.load_yaml to return empty dict (simulating no existing file)
            mock_data_loader.load_yaml.return_value = {}

            graph_processor._create_node_from_scratch(
                mock_node_path, sample_node_properties, sample_node_metadata, None
            )

            # Verify directory creation
            mock_data_writer.create_directory.assert_any_call(mock_node_path)
            mock_data_writer.create_directory.assert_any_call(mock_node_path / "source")

            # Verify validation was called
            mock_validate.assert_called_once_with(sample_node_properties, sample_node_metadata)

            # Verify file models were configured and saved
            assert sample_node_properties._filepath == mock_node_path / "properties.yaml"
            assert sample_node_metadata._filepath == mock_node_path / "metadata.yaml"

            # Verify yaml files were written (save() method calls DataWriter.write_yaml)
            assert mock_save_data_writer.write_yaml.call_count == 2

            # Verify clone was not called (no repo link)
            mock_clone.assert_not_called()

    def test_create_node_from_scratch_with_repo_clone(
        self, graph_processor, sample_node_properties, sample_node_metadata
    ):
        """Test _create_node_from_scratch with repository cloning."""
        mock_node_path = Path("/test/project/test-node")
        repo_link = "https://github.com/test/repo.git"

        with (
            patch("fluidize.core.modules.graph.processor.DataWriter"),
            patch.object(graph_processor, "_validate_and_warn_missing_fields"),
            patch.object(graph_processor, "_clone_repository") as mock_clone,
            patch("fluidize.core.utils.dataloader.data_loader.DataLoader") as mock_data_loader,
            patch("fluidize.core.utils.dataloader.data_writer.DataWriter"),
        ):
            mock_data_loader.load_yaml.return_value = {}

            graph_processor._create_node_from_scratch(
                mock_node_path, sample_node_properties, sample_node_metadata, repo_link
            )

            # Verify clone was called with correct parameters
            mock_clone.assert_called_once_with(repo_link, mock_node_path / "source")

    def test_validate_and_warn_missing_fields_complete_data(
        self, graph_processor, sample_node_properties, sample_node_metadata, capsys
    ):
        """Test validation with complete data produces only info messages."""
        graph_processor._validate_and_warn_missing_fields(sample_node_properties, sample_node_metadata)

        captured = capsys.readouterr()
        # Should not have any warning messages for complete data
        assert "Warning:" not in captured.out

    def test_validate_and_warn_missing_fields_missing_required(
        self, graph_processor, minimal_node_properties, minimal_node_metadata, capsys
    ):
        """Test validation warns about missing optional fields."""
        # Remove a required field
        minimal_node_properties.container_image = ""
        minimal_node_metadata.authors = []

        graph_processor._validate_and_warn_missing_fields(minimal_node_properties, minimal_node_metadata)

        captured = capsys.readouterr()
        assert "Warning: Required field 'container_image' is missing" in captured.out
        assert "Warning: Required field 'authors' is missing" in captured.out

    def test_validate_and_warn_missing_fields_missing_optional(
        self, graph_processor, minimal_node_properties, minimal_node_metadata, capsys
    ):
        """Test validation provides info about missing optional fields."""
        graph_processor._validate_and_warn_missing_fields(minimal_node_properties, minimal_node_metadata)

        captured = capsys.readouterr()
        assert "Info: Optional field 'image_name' not provided" in captured.out
        assert "Info: Optional field 'date' not provided" in captured.out

    def test_clone_repository_success(self, graph_processor, capsys):
        """Test successful repository cloning."""
        repo_link = "https://github.com/test/repo.git"
        source_path = Path("/test/source")

        with (
            patch("fluidize.core.modules.graph.processor.shutil.which", return_value="/usr/bin/git"),
            patch("fluidize.core.modules.graph.processor.subprocess.run") as mock_run,
        ):
            graph_processor._clone_repository(repo_link, source_path)

            mock_run.assert_called_once_with(
                ["/usr/bin/git", "clone", repo_link, str(source_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
            )

            captured = capsys.readouterr()
            assert "Successfully cloned repository" in captured.out

    def test_clone_repository_invalid_url(self, graph_processor, capsys):
        """Test repository cloning with invalid URL."""
        repo_link = "invalid-url"
        source_path = Path("/test/source")

        graph_processor._clone_repository(repo_link, source_path)

        captured = capsys.readouterr()
        assert "Warning: Invalid repository URL scheme" in captured.out

    def test_clone_repository_empty_url(self, graph_processor, capsys):
        """Test repository cloning with empty URL."""
        repo_link = "   "
        source_path = Path("/test/source")

        graph_processor._clone_repository(repo_link, source_path)

        captured = capsys.readouterr()
        assert "Warning: Empty repository link provided" in captured.out

    def test_clone_repository_git_not_found(self, graph_processor, capsys):
        """Test repository cloning when git is not available."""
        repo_link = "https://github.com/test/repo.git"
        source_path = Path("/test/source")

        with patch("fluidize.core.modules.graph.processor.shutil.which", return_value=None):
            graph_processor._clone_repository(repo_link, source_path)

            captured = capsys.readouterr()
            assert "Warning: git command not found" in captured.out

    def test_clone_repository_timeout(self, graph_processor, capsys):
        """Test repository cloning timeout."""
        import subprocess

        repo_link = "https://github.com/test/repo.git"
        source_path = Path("/test/source")

        with (
            patch("fluidize.core.modules.graph.processor.shutil.which", return_value="/usr/bin/git"),
            patch("fluidize.core.modules.graph.processor.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = subprocess.TimeoutExpired("git", 300)

            graph_processor._clone_repository(repo_link, source_path)

            captured = capsys.readouterr()
            assert "Warning: Repository clone timed out" in captured.out

    def test_clone_repository_command_failure(self, graph_processor, capsys):
        """Test repository cloning command failure."""
        import subprocess

        repo_link = "https://github.com/test/nonexistent.git"
        source_path = Path("/test/source")

        with (
            patch("fluidize.core.modules.graph.processor.shutil.which", return_value="/usr/bin/git"),
            patch("fluidize.core.modules.graph.processor.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = subprocess.CalledProcessError(128, "git", stderr="Repository not found")

            graph_processor._clone_repository(repo_link, source_path)

            captured = capsys.readouterr()
            assert "Warning: Failed to clone repository" in captured.out
            assert "Repository not found" in captured.out

    def test_insert_node_from_scratch_minimal_data(
        self,
        graph_processor,
        mock_path_finder,
        mock_graph_model,
        sample_project,
        minimal_node_properties,
        minimal_node_metadata,
    ):
        """Test insert_node_from_scratch with minimal required data."""
        mock_project_path = Path("/test/project")
        mock_node_path = Path("/test/project/minimal-node")

        mock_path_finder.get_project_path.return_value = mock_project_path
        mock_path_finder.get_node_path.return_value = mock_node_path

        mock_graph_instance = Mock()
        mock_graph_model.from_file.return_value = mock_graph_instance

        node = SampleGraphs.sample_nodes()[0]
        node.id = "minimal-node"

        with patch.object(graph_processor, "_create_node_from_scratch") as mock_create:
            result = graph_processor.insert_node_from_scratch(node, minimal_node_properties, minimal_node_metadata)

            assert result == node
            mock_create.assert_called_once_with(mock_node_path, minimal_node_properties, minimal_node_metadata, None)
