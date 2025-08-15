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
