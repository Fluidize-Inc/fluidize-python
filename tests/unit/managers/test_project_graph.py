"""Unit tests for ProjectGraph manager - project-scoped graph operations."""

import datetime
from unittest.mock import Mock

import pytest

from fluidize.core.types.node import author, nodeMetadata_simulation, nodeProperties_simulation, tag
from fluidize.core.types.parameters import Parameter
from fluidize.core.types.runs import RunStatus
from fluidize.managers.project_graph import ProjectGraph
from tests.fixtures.sample_graphs import SampleGraphs
from tests.fixtures.sample_projects import SampleProjects


class TestProjectGraph:
    """Test suite for ProjectGraph manager class."""

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
    def project_graph(self, mock_adapter, sample_project):
        """Create a ProjectGraph instance for testing."""
        return ProjectGraph(mock_adapter, sample_project)

    def test_init_with_graph_initialization(self, mock_adapter, sample_project):
        """Test ProjectGraph initialization triggers graph initialization."""
        mock_adapter.graph.ensure_graph_initialized = Mock()

        project_graph = ProjectGraph(mock_adapter, sample_project)

        assert project_graph.adapter is mock_adapter
        assert project_graph.project is sample_project
        mock_adapter.graph.ensure_graph_initialized.assert_called_once_with(sample_project)

    def test_init_without_graph_handler(self, sample_project):
        """Test initialization when adapter doesn't have graph handler."""
        adapter_without_graph = Mock()
        del adapter_without_graph.graph  # Remove graph attribute

        # Should not raise error
        project_graph = ProjectGraph(adapter_without_graph, sample_project)

        assert project_graph.adapter is adapter_without_graph
        assert project_graph.project is sample_project

    def test_init_without_ensure_method(self, sample_project):
        """Test initialization when graph handler doesn't have ensure method."""
        adapter = Mock()
        adapter.graph = Mock()
        del adapter.graph.ensure_graph_initialized  # Remove ensure method

        # Should not raise error
        project_graph = ProjectGraph(adapter, sample_project)

        assert project_graph.adapter is adapter
        assert project_graph.project is sample_project

    def test_get_graph_success(self, project_graph, mock_adapter):
        """Test successful graph retrieval."""
        expected_graph = SampleGraphs.complex_graph()
        mock_adapter.graph.get_graph.return_value = expected_graph

        result = project_graph.get()

        assert result == expected_graph
        mock_adapter.graph.get_graph.assert_called_once_with(project_graph.project)

    def test_get_empty_graph(self, project_graph, mock_adapter):
        """Test retrieving empty graph."""
        empty_graph = SampleGraphs.empty_graph()
        mock_adapter.graph.get_graph.return_value = empty_graph

        result = project_graph.get()

        assert result == empty_graph
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_add_node_success(self, project_graph, mock_adapter):
        """Test successful node addition."""
        node = SampleGraphs.sample_nodes()[0]
        mock_adapter.graph.insert_node.return_value = node

        result = project_graph.add_node(node)

        assert result == node
        mock_adapter.graph.insert_node.assert_called_once_with(
            project_graph.project,
            node,
            True,  # Default sim_global=True
        )

    def test_add_node_with_sim_global_false(self, project_graph, mock_adapter):
        """Test node addition with sim_global=False."""
        node = SampleGraphs.sample_nodes()[1]
        mock_adapter.graph.insert_node.return_value = node

        result = project_graph.add_node(node, sim_global=False)

        assert result == node
        mock_adapter.graph.insert_node.assert_called_once_with(project_graph.project, node, False)

    def test_add_node_from_scratch_success(self, project_graph, mock_adapter):
        """Test successful node creation from scratch."""
        node = SampleGraphs.sample_nodes()[0]

        # Create sample node properties
        node_properties = nodeProperties_simulation(
            container_image="python:3.9",
            simulation_mount_path="/app",
            source_output_folder="output",
            should_run=True,
            run_status=RunStatus.NOT_RUN,
            version="1.0",
        )

        # Create sample node metadata
        node_metadata = nodeMetadata_simulation(
            name="Test Simulation",
            id="test-sim-001",
            description="A test simulation node",
            date=datetime.date.today(),
            version="1.0",
            authors=[author(name="Test Author", institution="Test University")],
            tags=[tag(name="test", description="Test tag")],
            code_url="https://github.com/test/repo",
            paper_url="https://doi.org/10.1000/example.paper",
        )

        mock_adapter.graph.insert_node_from_scratch.return_value = node

        result = project_graph.add_node_from_scratch(node, node_properties, node_metadata)

        assert result == node
        mock_adapter.graph.insert_node_from_scratch.assert_called_once_with(
            project_graph.project,
            node,
            node_properties,
            node_metadata,
            None,  # Default repo_link=None
        )

    def test_add_node_from_scratch_with_repo_link(self, project_graph, mock_adapter):
        """Test node creation from scratch with repository link."""
        node = SampleGraphs.sample_nodes()[0]

        # Create minimal required properties and metadata
        node_properties = nodeProperties_simulation(container_image="python:3.9", simulation_mount_path="/app")

        node_metadata = nodeMetadata_simulation(
            name="Test Simulation",
            id="test-sim-002",
            description="A test simulation with repo",
            date=datetime.date.today(),
            version="1.0",
            authors=[author(name="Test Author", institution="Test University")],
            tags=[],
            code_url="https://github.com/test/repo",
            paper_url="https://doi.org/10.1000/example.paper",
        )

        repo_link = "https://github.com/test/example-repo.git"
        mock_adapter.graph.insert_node_from_scratch.return_value = node

        result = project_graph.add_node_from_scratch(node, node_properties, node_metadata, repo_link)

        assert result == node
        mock_adapter.graph.insert_node_from_scratch.assert_called_once_with(
            project_graph.project, node, node_properties, node_metadata, repo_link
        )

    def test_add_node_from_scratch_error_propagation(self, project_graph, mock_adapter):
        """Test that adapter errors are propagated for add_node_from_scratch operations."""
        node = SampleGraphs.sample_nodes()[0]

        node_properties = nodeProperties_simulation(container_image="python:3.9", simulation_mount_path="/app")

        node_metadata = nodeMetadata_simulation(
            name="Test Simulation",
            id="test-sim-003",
            description="A test simulation that will fail",
            date=datetime.date.today(),
            version="1.0",
            authors=[author(name="Test Author", institution="Test University")],
            tags=[],
            code_url="https://github.com/test/repo",
            paper_url="https://doi.org/10.1000/example.paper",
        )

        mock_adapter.graph.insert_node_from_scratch.side_effect = ValueError("Failed to create node from scratch")

        with pytest.raises(ValueError, match="Failed to create node from scratch"):
            project_graph.add_node_from_scratch(node, node_properties, node_metadata)

    def test_update_node_position_success(self, project_graph, mock_adapter):
        """Test successful node position update."""
        node = SampleGraphs.sample_nodes()[0]
        # Modify position for update test
        node.position.x = 500.0
        node.position.y = 600.0
        mock_adapter.graph.update_node_position.return_value = node

        result = project_graph.update_node_position(node)

        assert result == node
        mock_adapter.graph.update_node_position.assert_called_once_with(project_graph.project, node)

    def test_delete_node_success(self, project_graph, mock_adapter):
        """Test successful node deletion."""
        node_id = "test-node-to-delete"

        project_graph.delete_node(node_id)

        mock_adapter.graph.delete_node.assert_called_once_with(project_graph.project, node_id)

    def test_add_edge_success(self, project_graph, mock_adapter):
        """Test successful edge addition."""
        edge = SampleGraphs.sample_edges()[0]
        mock_adapter.graph.upsert_edge.return_value = edge

        result = project_graph.add_edge(edge)

        assert result == edge
        mock_adapter.graph.upsert_edge.assert_called_once_with(project_graph.project, edge)

    def test_delete_edge_success(self, project_graph, mock_adapter):
        """Test successful edge deletion."""
        edge_id = "test-edge-to-delete"

        project_graph.delete_edge(edge_id)

        mock_adapter.graph.delete_edge.assert_called_once_with(project_graph.project, edge_id)

    def test_adapter_error_propagation_get(self, project_graph, mock_adapter):
        """Test that adapter errors are propagated for get operations."""
        mock_adapter.graph.get_graph.side_effect = FileNotFoundError("Graph file not found")

        with pytest.raises(FileNotFoundError, match="Graph file not found"):
            project_graph.get()

    def test_adapter_error_propagation_add_node(self, project_graph, mock_adapter):
        """Test that adapter errors are propagated for add node operations."""
        node = SampleGraphs.sample_nodes()[0]
        mock_adapter.graph.insert_node.side_effect = ValueError("Invalid node data")

        with pytest.raises(ValueError, match="Invalid node data"):
            project_graph.add_node(node)

    def test_adapter_error_propagation_delete_node(self, project_graph, mock_adapter):
        """Test that adapter errors are propagated for delete node operations."""
        mock_adapter.graph.delete_node.side_effect = FileNotFoundError("Node not found")

        with pytest.raises(FileNotFoundError, match="Node not found"):
            project_graph.delete_node("non-existent-node")

    def test_adapter_error_propagation_add_edge(self, project_graph, mock_adapter):
        """Test that adapter errors are propagated for add edge operations."""
        edge = SampleGraphs.sample_edges()[0]
        mock_adapter.graph.upsert_edge.side_effect = ValueError("Invalid edge")

        with pytest.raises(ValueError, match="Invalid edge"):
            project_graph.add_edge(edge)

    def test_project_scoping(self, mock_adapter):
        """Test that different ProjectGraph instances are properly scoped to their projects."""
        project1 = SampleProjects.standard_project()
        project2 = SampleProjects.minimal_project()

        graph1 = ProjectGraph(mock_adapter, project1)
        graph2 = ProjectGraph(mock_adapter, project2)

        node = SampleGraphs.sample_nodes()[0]

        # Add node to first project graph
        graph1.add_node(node)

        # Add same node to second project graph
        graph2.add_node(node)

        # Verify each call was made with correct project context
        calls = mock_adapter.graph.insert_node.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == project1  # First call with project1
        assert calls[1][0][0] == project2  # Second call with project2

    def test_all_methods_delegate_to_adapter(self, project_graph, mock_adapter):
        """Test that all ProjectGraph methods properly delegate to adapter."""
        # Setup return values
        mock_graph_data = SampleGraphs.single_node_graph()
        mock_node = SampleGraphs.sample_nodes()[0]
        mock_edge = SampleGraphs.sample_edges()[0]

        mock_adapter.graph.get_graph.return_value = mock_graph_data
        mock_adapter.graph.insert_node.return_value = mock_node
        mock_adapter.graph.update_node_position.return_value = mock_node
        mock_adapter.graph.upsert_edge.return_value = mock_edge

        # Call all methods
        project_graph.get()
        project_graph.add_node(mock_node)
        project_graph.update_node_position(mock_node)
        project_graph.delete_node("test-id")
        project_graph.add_edge(mock_edge)
        project_graph.delete_edge("test-edge-id")

        # Verify all adapter methods were called
        mock_adapter.graph.get_graph.assert_called_once()
        mock_adapter.graph.insert_node.assert_called_once()
        mock_adapter.graph.update_node_position.assert_called_once()
        mock_adapter.graph.delete_node.assert_called_once()
        mock_adapter.graph.upsert_edge.assert_called_once()
        mock_adapter.graph.delete_edge.assert_called_once()

    def test_add_node_from_scratch_delegates_to_adapter(self, project_graph, mock_adapter):
        """Test that add_node_from_scratch properly delegates to adapter."""
        node = SampleGraphs.sample_nodes()[0]

        node_properties = nodeProperties_simulation(container_image="python:3.9", simulation_mount_path="/app")

        node_metadata = nodeMetadata_simulation(
            name="Delegation Test",
            id="delegation-test",
            description="Test adapter delegation",
            date=datetime.date.today(),
            version="1.0",
            authors=[author(name="Test Author", institution="Test University")],
            tags=[],
            code_url="https://github.com/test/repo",
            paper_url="https://doi.org/10.1000/example.paper",
        )

        mock_adapter.graph.insert_node_from_scratch.return_value = node

        result = project_graph.add_node_from_scratch(node, node_properties, node_metadata)

        assert result == node
        mock_adapter.graph.insert_node_from_scratch.assert_called_once_with(
            project_graph.project, node, node_properties, node_metadata, None
        )

    def test_project_context_consistency(self, project_graph, mock_adapter):
        """Test that the same project context is used for all operations."""
        project = project_graph.project
        node = SampleGraphs.sample_nodes()[0]
        edge = SampleGraphs.sample_edges()[0]

        # Setup return values
        mock_adapter.graph.get_graph.return_value = SampleGraphs.empty_graph()
        mock_adapter.graph.insert_node.return_value = node
        mock_adapter.graph.update_node_position.return_value = node
        mock_adapter.graph.upsert_edge.return_value = edge

        # Perform various operations
        project_graph.get()
        project_graph.add_node(node)
        project_graph.update_node_position(node)
        project_graph.delete_node("test-id")
        project_graph.add_edge(edge)
        project_graph.delete_edge("test-edge-id")

        # Verify project context was passed consistently
        all_calls = [
            mock_adapter.graph.get_graph.call_args_list,
            mock_adapter.graph.insert_node.call_args_list,
            mock_adapter.graph.update_node_position.call_args_list,
            mock_adapter.graph.delete_node.call_args_list,
            mock_adapter.graph.upsert_edge.call_args_list,
            mock_adapter.graph.delete_edge.call_args_list,
        ]

        # All calls should include the same project as first argument
        for call_list in all_calls:
            if call_list:  # If method was called
                assert call_list[0][0][0] == project

    def test_get_parameters_success(self, project_graph, mock_adapter):
        """Test successful parameter retrieval through ProjectGraph."""
        node_id = "test-node-id"
        expected_parameters = [
            Parameter(
                name="test_param",
                value="test_value",
                type="text",
                label="Test Parameter",
                description="A test parameter",
            )
        ]

        mock_adapter.graph.get_parameters.return_value = expected_parameters

        result = project_graph.get_parameters(node_id)

        assert result == expected_parameters
        mock_adapter.graph.get_parameters.assert_called_once_with(project_graph.project, node_id)

    def test_upsert_parameter_success(self, project_graph, mock_adapter):
        """Test successful parameter upsert through ProjectGraph."""
        node_id = "test-node-id"
        parameter = Parameter(
            name="new_param", value="new_value", type="text", label="New Parameter", description="A new parameter"
        )

        mock_adapter.graph.upsert_parameter.return_value = parameter

        result = project_graph.upsert_parameter(node_id, parameter)

        assert result == parameter
        mock_adapter.graph.upsert_parameter.assert_called_once_with(project_graph.project, node_id, parameter)

    def test_set_parameters_success(self, project_graph, mock_adapter):
        """Test successful parameters setting through ProjectGraph."""
        node_id = "test-node-id"
        parameters = [
            Parameter(name="param1", value="value1", type="text", label="Parameter 1", description="First parameter"),
            Parameter(
                name="param2", value="value2", type="number", label="Parameter 2", description="Second parameter"
            ),
        ]

        mock_adapter.graph.set_parameters.return_value = parameters

        result = project_graph.set_parameters(node_id, parameters)

        assert result == parameters
        mock_adapter.graph.set_parameters.assert_called_once_with(project_graph.project, node_id, parameters)

    def test_parameter_methods_error_propagation(self, project_graph, mock_adapter):
        """Test that parameter method errors are propagated."""
        node_id = "test-node-id"
        parameter = Parameter(
            name="test_param", value="test_value", type="text", label="Test Parameter", description="A test parameter"
        )

        # Test get_parameters error propagation
        mock_adapter.graph.get_parameters.side_effect = FileNotFoundError("Parameters file not found")
        with pytest.raises(FileNotFoundError, match="Parameters file not found"):
            project_graph.get_parameters(node_id)

        # Test upsert_parameter error propagation
        mock_adapter.graph.upsert_parameter.side_effect = ValueError("Invalid parameter data")
        with pytest.raises(ValueError, match="Invalid parameter data"):
            project_graph.upsert_parameter(node_id, parameter)

        # Test set_parameters error propagation
        mock_adapter.graph.set_parameters.side_effect = PermissionError("Cannot write to parameters file")
        with pytest.raises(PermissionError, match="Cannot write to parameters file"):
            project_graph.set_parameters(node_id, [parameter])

    def test_parameter_methods_use_correct_project_context(self, mock_adapter):
        """Test that parameter methods use correct project context."""
        project1 = SampleProjects.standard_project()
        project2 = SampleProjects.minimal_project()

        graph1 = ProjectGraph(mock_adapter, project1)
        graph2 = ProjectGraph(mock_adapter, project2)

        parameter = Parameter(
            name="test_param", value="test_value", type="text", label="Test Parameter", description="A test parameter"
        )

        mock_adapter.graph.get_parameters.return_value = [parameter]
        mock_adapter.graph.upsert_parameter.return_value = parameter
        mock_adapter.graph.set_parameters.return_value = [parameter]

        # Call parameter methods on different project graphs
        graph1.get_parameters("node1")
        graph2.get_parameters("node2")

        graph1.upsert_parameter("node1", parameter)
        graph2.upsert_parameter("node2", parameter)

        graph1.set_parameters("node1", [parameter])
        graph2.set_parameters("node2", [parameter])

        # Verify correct project contexts were used
        get_calls = mock_adapter.graph.get_parameters.call_args_list
        upsert_calls = mock_adapter.graph.upsert_parameter.call_args_list
        set_calls = mock_adapter.graph.set_parameters.call_args_list

        assert len(get_calls) == 2
        assert get_calls[0][0][0] == project1
        assert get_calls[1][0][0] == project2

        assert len(upsert_calls) == 2
        assert upsert_calls[0][0][0] == project1
        assert upsert_calls[1][0][0] == project2

        assert len(set_calls) == 2
        assert set_calls[0][0][0] == project1
        assert set_calls[1][0][0] == project2

    def test_show_parameters_success(self, project_graph, mock_adapter):
        """Test successful parameter display through ProjectGraph."""
        node_id = "test-node-id"
        expected_output = "Parameters for node 'test-node-id':\n\nParameter 1:\n  Name: test_param\n  Value: test_value"

        mock_adapter.graph.show_parameters.return_value = expected_output

        result = project_graph.show_parameters(node_id)

        assert result == expected_output
        mock_adapter.graph.show_parameters.assert_called_once_with(project_graph.project, node_id)
