"""Unit tests for NodeManager - node-scoped operations."""

from unittest.mock import Mock, patch

import pytest

from fluidize.core.types.graph import GraphData, GraphNode, Position, graphNodeData
from fluidize.core.types.parameters import Parameter
from fluidize.managers.node import NodeManager
from tests.fixtures.sample_projects import SampleProjects


class TestNodeManager:
    """Test suite for NodeManager class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter with graph handler."""
        adapter = Mock()
        adapter.graph = Mock()
        return adapter

    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        return SampleProjects.standard_project()

    @pytest.fixture
    def sample_node(self):
        """Sample graph node for testing."""
        return GraphNode(
            id="test-node-001",
            position=Position(x=100.0, y=200.0),
            data=graphNodeData(label="Test Node", simulation_id="test-sim-001"),
            type="simulation",
        )

    @pytest.fixture
    def node_manager(self, mock_adapter, sample_project):
        """Create a NodeManager instance for testing."""
        return NodeManager(mock_adapter, sample_project, "test-node-001")

    def test_init(self, mock_adapter, sample_project):
        """Test NodeManager initialization."""
        node_manager = NodeManager(mock_adapter, sample_project, "test-node-001")

        assert node_manager.adapter is mock_adapter
        assert node_manager.project is sample_project
        assert node_manager.node_id == "test-node-001"

    def test_get_node_success(self, node_manager, mock_adapter, sample_node):
        """Test successful node retrieval."""
        graph_data = GraphData(nodes=[sample_node], edges=[])
        mock_adapter.graph.get_graph.return_value = graph_data

        result = node_manager.get_node()

        assert result == sample_node
        mock_adapter.graph.get_graph.assert_called_once_with(node_manager.project)

    def test_get_node_not_found(self, node_manager, mock_adapter):
        """Test node not found error."""
        graph_data = GraphData(nodes=[], edges=[])
        mock_adapter.graph.get_graph.return_value = graph_data

        with pytest.raises(ValueError, match="Node with ID 'test-node-001' not found"):
            node_manager.get_node()

    def test_exists_true(self, node_manager, mock_adapter, sample_node):
        """Test exists returns True when node exists."""
        graph_data = GraphData(nodes=[sample_node], edges=[])
        mock_adapter.graph.get_graph.return_value = graph_data

        assert node_manager.exists() is True

    def test_exists_false(self, node_manager, mock_adapter):
        """Test exists returns False when node doesn't exist."""
        graph_data = GraphData(nodes=[], edges=[])
        mock_adapter.graph.get_graph.return_value = graph_data

        assert node_manager.exists() is False

    def test_delete(self, node_manager, mock_adapter):
        """Test node deletion."""
        node_manager.delete()

        mock_adapter.graph.delete_node.assert_called_once_with(node_manager.project, "test-node-001")

    def test_update_position(self, node_manager, mock_adapter, sample_node):
        """Test node position update."""
        graph_data = GraphData(nodes=[sample_node], edges=[])
        mock_adapter.graph.get_graph.return_value = graph_data
        mock_adapter.graph.update_node_position.return_value = sample_node

        result = node_manager.update_position(300.0, 400.0)

        assert result == sample_node
        assert sample_node.position.x == 300.0
        assert sample_node.position.y == 400.0
        mock_adapter.graph.update_node_position.assert_called_once()

    @patch("fluidize.managers.node.nodeMetadata_simulation")
    def test_get_metadata(self, mock_metadata_class, node_manager):
        """Test getting node metadata."""
        mock_metadata = Mock()
        mock_metadata_class.from_file.return_value = mock_metadata

        result = node_manager.get_metadata()

        assert result == mock_metadata
        mock_metadata_class.from_file.assert_called_once()

    @patch("fluidize.managers.node.nodeProperties_simulation")
    def test_get_properties(self, mock_properties_class, node_manager):
        """Test getting node properties."""
        mock_properties = Mock()
        mock_properties_class.from_file.return_value = mock_properties

        result = node_manager.get_properties()

        assert result == mock_properties
        mock_properties_class.from_file.assert_called_once()

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_get_parameters_model(self, mock_parameters_class, node_manager):
        """Test getting node parameters model."""
        mock_parameters = Mock()
        mock_parameters.parameters = []
        mock_parameters_class.from_file.return_value = mock_parameters

        result = node_manager.get_parameters_model()

        assert result == mock_parameters
        mock_parameters_class.from_file.assert_called_once()

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_get_parameters(self, mock_parameters_class, node_manager):
        """Test getting node parameters list."""
        mock_parameter = Parameter(
            value="test_value", description="Test parameter", type="text", label="Test", name="test_param"
        )
        mock_parameters = Mock()
        mock_parameters.parameters = [mock_parameter]
        mock_parameters_class.from_file.return_value = mock_parameters

        result = node_manager.get_parameters()

        assert result == [mock_parameter]

    def test_get_parameter_found(self, node_manager):
        """Test getting a specific parameter by name."""
        mock_parameter = Parameter(
            value="test_value", description="Test parameter", type="text", label="Test", name="test_param"
        )

        with patch.object(node_manager, "get_parameters", return_value=[mock_parameter]):
            result = node_manager.get_parameter("test_param")
            assert result == mock_parameter

    def test_get_parameter_not_found(self, node_manager):
        """Test getting a parameter that doesn't exist."""
        with patch.object(node_manager, "get_parameters", return_value=[]):
            result = node_manager.get_parameter("nonexistent")
            assert result is None

    def test_validate_all_valid(self, node_manager, sample_node):
        """Test validation when all components are valid."""

        with (
            patch.object(node_manager, "get_node", return_value=sample_node),
            patch.object(node_manager, "get_metadata"),
            patch.object(node_manager, "get_properties"),
            patch.object(node_manager, "get_parameters", return_value=[]),
        ):
            result = node_manager.validate()

            assert result["valid"] is True
            assert result["graph_node_exists"] is True
            assert result["metadata_exists"] is True
            assert result["properties_exists"] is True
            assert result["parameters_exists"] is True
            assert len(result["errors"]) == 0

    def test_validate_with_errors(self, node_manager):
        """Test validation when there are errors."""
        with (
            patch.object(node_manager, "get_node", side_effect=ValueError("Node not found")),
            patch.object(node_manager, "get_metadata", side_effect=FileNotFoundError("Metadata not found")),
            patch.object(node_manager, "get_properties"),
            patch.object(node_manager, "get_parameters", return_value=[]),
        ):
            result = node_manager.validate()

            assert result["valid"] is False
            assert result["graph_node_exists"] is False
            assert result["metadata_exists"] is False
            assert len(result["errors"]) == 2
            assert "Node not found" in result["errors"][0]
            assert "Metadata error: Metadata not found" in result["errors"][1]

    def test_id_property(self, node_manager):
        """Test id property returns node_id."""
        assert node_manager.id == "test-node-001"

    def test_data_property(self, node_manager, mock_adapter, sample_node):
        """Test data property returns node data."""
        graph_data = GraphData(nodes=[sample_node], edges=[])
        mock_adapter.graph.get_graph.return_value = graph_data

        result = node_manager.data

        assert result == sample_node.data

    @patch("fluidize.managers.node.nodeMetadata_simulation")
    def test_update_metadata(self, mock_metadata_class, node_manager):
        """Test updating node metadata."""
        mock_metadata = Mock()
        mock_metadata_class.from_file.return_value = mock_metadata

        result = node_manager.update_metadata(name="New Name", description="New description")

        assert result == mock_metadata
        mock_metadata.edit.assert_called_once_with(name="New Name", description="New description")

    @patch("fluidize.managers.node.nodeMetadata_simulation")
    @patch("fluidize.managers.node.PathFinder")
    def test_save_metadata(self, mock_path_finder, mock_metadata_class, node_manager):
        """Test saving metadata to file."""
        mock_node_path = Mock()
        mock_path_finder.get_node_path.return_value = mock_node_path
        mock_metadata = Mock()

        node_manager.save_metadata(mock_metadata)

        mock_path_finder.get_node_path.assert_called_once_with(node_manager.project, "test-node-001")
        mock_metadata.save.assert_called_once_with(mock_node_path)

    @patch("fluidize.managers.node.nodeProperties_simulation")
    def test_update_properties(self, mock_properties_class, node_manager):
        """Test updating node properties."""
        mock_properties = Mock()
        mock_properties_class.from_file.return_value = mock_properties

        result = node_manager.update_properties(container_image="new:tag", should_run=False)

        assert result == mock_properties
        mock_properties.edit.assert_called_once_with(container_image="new:tag", should_run=False)

    @patch("fluidize.managers.node.nodeProperties_simulation")
    @patch("fluidize.managers.node.PathFinder")
    def test_save_properties(self, mock_path_finder, mock_properties_class, node_manager):
        """Test saving properties to file."""
        mock_node_path = Mock()
        mock_path_finder.get_node_path.return_value = mock_node_path
        mock_properties = Mock()

        node_manager.save_properties(mock_properties)

        mock_path_finder.get_node_path.assert_called_once_with(node_manager.project, "test-node-001")
        mock_properties.save.assert_called_once_with(mock_node_path)

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_update_parameter_existing(self, mock_parameters_class, node_manager):
        """Test updating an existing parameter."""
        existing_param = Parameter(
            value="old_value", description="Old desc", type="text", label="Old", name="test_param"
        )
        mock_parameters = Mock()
        mock_parameters.parameters = [existing_param]
        mock_parameters_class.from_file.return_value = mock_parameters

        new_param = Parameter(value="new_value", description="New desc", type="text", label="New", name="test_param")

        result = node_manager.update_parameter(new_param)

        assert result == new_param
        assert existing_param.value == "new_value"
        assert existing_param.description == "New desc"
        mock_parameters.save.assert_called_once()

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_update_parameter_new(self, mock_parameters_class, node_manager):
        """Test adding a new parameter."""
        mock_parameters = Mock()
        mock_parameters.parameters = []
        mock_parameters_class.from_file.return_value = mock_parameters

        new_param = Parameter(value="new_value", description="New desc", type="text", label="New", name="new_param")

        result = node_manager.update_parameter(new_param)

        assert result == new_param
        assert new_param in mock_parameters.parameters
        mock_parameters.save.assert_called_once()

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_update_parameter_with_location(self, mock_parameters_class, node_manager):
        """Test updating parameter with location extension."""
        existing_param = Parameter(
            value="old_value", description="Old desc", type="text", label="Old", name="test_param", location=["old"]
        )
        mock_parameters = Mock()
        mock_parameters.parameters = [existing_param]
        mock_parameters_class.from_file.return_value = mock_parameters

        new_param = Parameter(
            value="new_value",
            description="New desc",
            type="text",
            label="New",
            name="test_param",
            location=["new", "location"],
        )

        node_manager.update_parameter(new_param)

        assert existing_param.location == ["old", "new", "location"]

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_set_parameters(self, mock_parameters_class, node_manager):
        """Test replacing all parameters."""
        mock_parameters = Mock()
        mock_parameters.parameters = []
        mock_parameters_class.from_file.return_value = mock_parameters

        new_params = [
            Parameter(value="val1", description="desc1", type="text", label="label1", name="param1"),
            Parameter(value="val2", description="desc2", type="text", label="label2", name="param2"),
        ]

        result = node_manager.set_parameters(new_params)

        assert result == new_params
        assert mock_parameters.parameters == new_params
        mock_parameters.save.assert_called_once()

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_remove_parameter_success(self, mock_parameters_class, node_manager):
        """Test successfully removing a parameter."""
        param1 = Parameter(value="val1", description="desc1", type="text", label="label1", name="param1")
        param2 = Parameter(value="val2", description="desc2", type="text", label="label2", name="param2")

        mock_parameters = Mock()
        mock_parameters.parameters = [param1, param2]
        mock_parameters_class.from_file.return_value = mock_parameters

        result = node_manager.remove_parameter("param1")

        assert result is True
        assert mock_parameters.parameters == [param2]
        mock_parameters.save.assert_called_once()

    @patch("fluidize.managers.node.nodeParameters_simulation")
    def test_remove_parameter_not_found(self, mock_parameters_class, node_manager):
        """Test removing a parameter that doesn't exist."""
        param1 = Parameter(value="val1", description="desc1", type="text", label="label1", name="param1")

        mock_parameters = Mock()
        mock_parameters.parameters = [param1]
        mock_parameters_class.from_file.return_value = mock_parameters

        result = node_manager.remove_parameter("nonexistent")

        assert result is False
        assert mock_parameters.parameters == [param1]
        mock_parameters.save.assert_not_called()

    def test_show_parameters_empty(self, node_manager):
        """Test showing parameters when no parameters exist."""
        with patch.object(node_manager, "get_parameters", return_value=[]):
            result = node_manager.show_parameters()
            assert result == "No parameters found for node 'test-node-001'"

    def test_show_parameters_with_data(self, node_manager):
        """Test showing parameters with data."""
        param1 = Parameter(
            value="value1",
            description="Description 1",
            type="text",
            label="Label 1",
            name="param1",
            latex="\\alpha",
            location=["section1"],
            scope="global",
        )
        param2 = Parameter(value="value2", description="Description 2", type="number", label="Label 2", name="param2")

        with patch.object(node_manager, "get_parameters", return_value=[param1, param2]):
            result = node_manager.show_parameters()

            assert "Parameters for node 'test-node-001':" in result
            assert "Parameter 1:" in result
            assert "Name: param1" in result
            assert "Value: value1" in result
            assert "LaTeX: \\alpha" in result
            assert "Location: ['section1']" in result
            assert "Scope: global" in result
            assert "Parameter 2:" in result
            assert "Name: param2" in result

    @patch("fluidize.managers.node.PathFinder")
    def test_get_node_directory(self, mock_path_finder, node_manager):
        """Test getting node directory path."""
        mock_path = Mock()
        mock_path_finder.get_node_path.return_value = mock_path

        result = node_manager.get_node_directory()

        assert result == mock_path
        mock_path_finder.get_node_path.assert_called_once_with(node_manager.project, "test-node-001")

    @patch("fluidize.managers.node.PathFinder")
    def test_get_metadata_path(self, mock_path_finder, node_manager):
        """Test getting metadata file path."""
        mock_node_path = Mock()
        mock_path_finder.get_node_path.return_value = mock_node_path

        # Mock the __truediv__ method to handle the / operator
        mock_node_path.__truediv__ = Mock(return_value="mocked_metadata_path")

        node_manager.get_metadata_path()

        mock_path_finder.get_node_path.assert_called_once_with(node_manager.project, "test-node-001")
        mock_node_path.__truediv__.assert_called_once()

    @patch("fluidize.managers.node.PathFinder")
    def test_get_properties_path(self, mock_path_finder, node_manager):
        """Test getting properties file path."""
        mock_path = Mock()
        mock_path_finder.get_properties_path.return_value = mock_path

        result = node_manager.get_properties_path()

        assert result == mock_path
        mock_path_finder.get_properties_path.assert_called_once_with(node_manager.project, "test-node-001")

    @patch("fluidize.managers.node.PathFinder")
    def test_get_parameters_path(self, mock_path_finder, node_manager):
        """Test getting parameters file path."""
        mock_path = Mock()
        mock_path_finder.get_node_parameters_path.return_value = mock_path

        result = node_manager.get_parameters_path()

        assert result == mock_path
        mock_path_finder.get_node_parameters_path.assert_called_once_with(node_manager.project, "test-node-001")

    def test_to_dict_success(self, node_manager, sample_node):
        """Test converting node to dictionary successfully."""
        mock_metadata = Mock()
        mock_metadata.model_dump.return_value = {"name": "Test Node"}
        mock_properties = Mock()
        mock_properties.model_dump.return_value = {"container_image": "test:latest"}
        mock_parameter = Mock()
        mock_parameter.model_dump.return_value = {"name": "param1", "value": "value1"}

        with (
            patch.object(node_manager, "get_node", return_value=sample_node),
            patch.object(node_manager, "get_metadata", return_value=mock_metadata),
            patch.object(node_manager, "get_properties", return_value=mock_properties),
            patch.object(node_manager, "get_parameters", return_value=[mock_parameter]),
            patch.object(node_manager, "get_node_directory", return_value="/path/to/node"),
            patch.object(node_manager, "get_metadata_path", return_value="/path/to/metadata.yaml"),
            patch.object(node_manager, "get_properties_path", return_value="/path/to/properties.yaml"),
            patch.object(node_manager, "get_parameters_path", return_value="/path/to/parameters.json"),
        ):
            result = node_manager.to_dict()

            assert "graph_node" in result
            assert "metadata" in result
            assert "properties" in result
            assert "parameters" in result
            assert "paths" in result
            assert result["metadata"] == {"name": "Test Node"}
            assert result["properties"] == {"container_image": "test:latest"}
            assert len(result["parameters"]) == 1

    def test_to_dict_error(self, node_manager):
        """Test to_dict when an error occurs."""
        with patch.object(node_manager, "get_node", side_effect=Exception("Test error")):
            result = node_manager.to_dict()

            assert "error" in result
            assert result["error"] == "Test error"
            assert result["node_id"] == "test-node-001"
            assert result["project"] == node_manager.project.id
