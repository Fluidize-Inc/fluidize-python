"""Unit tests for Project wrapper - enhanced project interface with graph property."""

from unittest.mock import Mock

import pytest

from fluidize.managers.project_graph import ProjectGraph
from fluidize.managers.project_manager import Project
from tests.fixtures.sample_projects import SampleProjects


class TestProject:
    """Test suite for Project wrapper class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter for testing."""
        adapter = Mock()
        adapter.graph = Mock()
        return adapter

    @pytest.fixture
    def sample_project_summary(self):
        """Sample ProjectSummary for testing."""
        return SampleProjects.standard_project()

    @pytest.fixture
    def project_wrapper(self, mock_adapter, sample_project_summary):
        """Create a Project wrapper instance for testing."""
        return Project(mock_adapter, sample_project_summary)

    def test_init(self, mock_adapter, sample_project_summary):
        """Test Project wrapper initialization."""
        project = Project(mock_adapter, sample_project_summary)

        assert project._adapter is mock_adapter
        assert project._project_summary is sample_project_summary
        assert project._graph is None  # Lazy loading

    def test_graph_property_lazy_initialization(self, project_wrapper, mock_adapter):
        """Test that graph property is lazily initialized."""
        assert project_wrapper._graph is None

        # Access graph property
        graph = project_wrapper.graph

        assert isinstance(graph, ProjectGraph)
        assert project_wrapper._graph is graph  # Cached
        assert graph.adapter is mock_adapter
        assert graph.project is project_wrapper._project_summary

    def test_graph_property_caching(self, project_wrapper):
        """Test that graph property is cached after first access."""
        # First access
        graph1 = project_wrapper.graph

        # Second access should return same instance
        graph2 = project_wrapper.graph

        assert graph1 is graph2

    def test_id_property_delegation(self, project_wrapper, sample_project_summary):
        """Test that id property delegates to ProjectSummary."""
        assert project_wrapper.id == sample_project_summary.id

    def test_label_property_delegation(self, project_wrapper, sample_project_summary):
        """Test that label property delegates to ProjectSummary."""
        assert project_wrapper.label == sample_project_summary.label

    def test_description_property_delegation(self, project_wrapper, sample_project_summary):
        """Test that description property delegates to ProjectSummary."""
        assert project_wrapper.description == sample_project_summary.description

    def test_location_property_delegation(self, project_wrapper, sample_project_summary):
        """Test that location property delegates to ProjectSummary."""
        assert project_wrapper.location == sample_project_summary.location

    def test_status_property_delegation(self, project_wrapper, sample_project_summary):
        """Test that status property delegates to ProjectSummary."""
        assert project_wrapper.status == sample_project_summary.status

    def test_metadata_version_property_delegation(self, project_wrapper, sample_project_summary):
        """Test that metadata_version property delegates to ProjectSummary."""
        assert project_wrapper.metadata_version == sample_project_summary.metadata_version

    def test_created_at_property_with_attribute(self, mock_adapter):
        """Test created_at property when attribute exists."""
        # Create a mock object that has the timestamp attribute
        from unittest.mock import Mock

        project_summary = Mock()
        project_summary.id = "test-project"
        project_summary.metadata_version = "1.0"
        project_summary.label = "Test Project"
        project_summary.description = "Test Description"
        project_summary.location = "/test/location"
        project_summary.status = "active"
        project_summary.created_at = "2024-01-01T00:00:00Z"

        project = Project(mock_adapter, project_summary)

        assert project.created_at == "2024-01-01T00:00:00Z"

    def test_created_at_property_without_attribute(self, project_wrapper):
        """Test created_at property when attribute doesn't exist."""
        # Standard project doesn't have created_at
        assert project_wrapper.created_at is None

    def test_updated_at_property_with_attribute(self, mock_adapter):
        """Test updated_at property when attribute exists."""
        # Create a mock object that has the timestamp attribute
        from unittest.mock import Mock

        project_summary = Mock()
        project_summary.id = "test-project"
        project_summary.metadata_version = "1.0"
        project_summary.label = "Test Project"
        project_summary.description = "Test Description"
        project_summary.location = "/test/location"
        project_summary.status = "active"
        project_summary.updated_at = "2024-01-01T12:00:00Z"

        project = Project(mock_adapter, project_summary)

        assert project.updated_at == "2024-01-01T12:00:00Z"

    def test_updated_at_property_without_attribute(self, project_wrapper):
        """Test updated_at property when attribute doesn't exist."""
        # Standard project doesn't have updated_at
        assert project_wrapper.updated_at is None

    def test_to_dict_complete_project(self, project_wrapper, sample_project_summary):
        """Test to_dict with complete project data."""
        result = project_wrapper.to_dict()

        expected = {
            "id": sample_project_summary.id,
            "label": sample_project_summary.label,
            "description": sample_project_summary.description,
            "location": sample_project_summary.location,
            "status": sample_project_summary.status,
            "metadata_version": sample_project_summary.metadata_version,
            "created_at": None,  # Not set in standard project
            "updated_at": None,  # Not set in standard project
        }

        assert result == expected

    def test_to_dict_minimal_project(self, mock_adapter):
        """Test to_dict with minimal project data."""
        minimal_summary = SampleProjects.minimal_project()
        project = Project(mock_adapter, minimal_summary)

        result = project.to_dict()

        # Check individual fields since minimal project may have different None/empty behavior
        assert result["id"] == minimal_summary.id
        assert result["metadata_version"] == minimal_summary.metadata_version
        assert result["created_at"] is None
        assert result["updated_at"] is None
        # Other fields should be None for minimal project
        assert result["label"] is None or result["label"] == getattr(minimal_summary, "label", None)
        assert result["description"] is None or result["description"] == getattr(minimal_summary, "description", None)
        assert result["location"] is None or result["location"] == getattr(minimal_summary, "location", None)
        assert result["status"] is None or result["status"] == getattr(minimal_summary, "status", None)

    def test_to_dict_with_timestamps(self, mock_adapter):
        """Test to_dict with timestamp attributes."""
        # Create a mock object that has timestamp attributes
        from unittest.mock import Mock

        project_summary = Mock()
        project_summary.id = "test-project"
        project_summary.metadata_version = "1.0"
        project_summary.label = "Test Project"
        project_summary.description = "Test Description"
        project_summary.location = "/test/location"
        project_summary.status = "active"
        project_summary.created_at = "2024-01-01T00:00:00Z"
        project_summary.updated_at = "2024-01-01T12:00:00Z"

        project = Project(mock_adapter, project_summary)

        result = project.to_dict()

        assert result["created_at"] == "2024-01-01T00:00:00Z"
        assert result["updated_at"] == "2024-01-01T12:00:00Z"

    def test_repr(self, project_wrapper, sample_project_summary):
        """Test __repr__ method."""
        result = repr(project_wrapper)
        expected = f"Project(id='{sample_project_summary.id}', label='{sample_project_summary.label}')"
        assert result == expected

    def test_repr_with_none_label(self, mock_adapter):
        """Test __repr__ method when label is None."""
        minimal_summary = SampleProjects.minimal_project()
        project = Project(mock_adapter, minimal_summary)

        result = repr(project)
        # Handle case where minimal project might have label=None or no label attribute
        label_value = getattr(minimal_summary, "label", None)
        expected = f"Project(id='{minimal_summary.id}', label='{label_value}')"
        assert result == expected

    def test_str_with_label(self, project_wrapper, sample_project_summary):
        """Test __str__ method with label."""
        result = str(project_wrapper)
        expected = f"Project {sample_project_summary.id}: {sample_project_summary.label}"
        assert result == expected

    def test_str_without_label(self, mock_adapter):
        """Test __str__ method without label."""
        minimal_summary = SampleProjects.minimal_project()
        project = Project(mock_adapter, minimal_summary)

        result = str(project)
        expected = f"Project {minimal_summary.id}: No label"
        assert result == expected

    def test_property_access_patterns(self, project_wrapper):
        """Test that all properties can be accessed without errors."""
        # Test all property access
        properties_to_test = [
            "id",
            "label",
            "description",
            "location",
            "status",
            "metadata_version",
            "created_at",
            "updated_at",
        ]

        for prop in properties_to_test:
            # Should not raise any exceptions
            value = getattr(project_wrapper, prop)
            # Value can be None or string, but should be accessible
            assert value is None or isinstance(value, str)

    def test_project_summary_preservation(self, project_wrapper, sample_project_summary):
        """Test that original ProjectSummary is preserved and accessible."""
        # The wrapper should not modify the original ProjectSummary
        assert project_wrapper._project_summary is sample_project_summary

        # All properties should match the original
        assert project_wrapper.id == sample_project_summary.id
        assert project_wrapper.label == sample_project_summary.label
        assert project_wrapper.description == sample_project_summary.description
        assert project_wrapper.location == sample_project_summary.location
        assert project_wrapper.status == sample_project_summary.status
        assert project_wrapper.metadata_version == sample_project_summary.metadata_version

    def test_adapter_preservation(self, project_wrapper, mock_adapter):
        """Test that adapter reference is preserved for graph operations."""
        assert project_wrapper._adapter is mock_adapter

        # Graph property should use the same adapter
        graph = project_wrapper.graph
        assert graph.adapter is mock_adapter

    def test_graph_integration(self, project_wrapper, mock_adapter, sample_project_summary):
        """Test integration between Project wrapper and ProjectGraph."""
        # Access graph
        graph = project_wrapper.graph

        # Verify proper integration
        assert isinstance(graph, ProjectGraph)
        assert graph.adapter is mock_adapter
        assert graph.project is sample_project_summary

        # Verify graph initialization was called
        if hasattr(mock_adapter.graph, "ensure_graph_initialized"):
            mock_adapter.graph.ensure_graph_initialized.assert_called_with(sample_project_summary)

    @pytest.mark.parametrize("project_fixture", ["standard_project", "minimal_project", "project_with_special_chars"])
    def test_wrapper_with_different_project_types(self, mock_adapter, project_fixture):
        """Test Project wrapper with different types of ProjectSummary objects."""
        project_summary = getattr(SampleProjects, project_fixture)()
        project = Project(mock_adapter, project_summary)

        # Basic functionality should work for all project types
        assert project.id == project_summary.id
        assert project.metadata_version == project_summary.metadata_version

        # Graph property should be accessible
        graph = project.graph
        assert isinstance(graph, ProjectGraph)

        # String representations should work
        repr_result = repr(project)
        str_result = str(project)
        assert isinstance(repr_result, str)
        assert isinstance(str_result, str)
        assert project_summary.id in repr_result
        assert project_summary.id in str_result
