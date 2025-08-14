"""Unit tests for ProjectsHandler - local adapter projects interface."""

from unittest.mock import Mock, patch

import pytest

from fluidize.adapters.local.projects import ProjectsHandler
from fluidize.core.types.project import ProjectSummary
from tests.fixtures.sample_projects import SampleProjects


class TestProjectsHandler:
    """Test suite for ProjectsHandler class."""

    @pytest.fixture
    def mock_processor(self):
        """Create a mock ProjectProcessor for testing."""
        with patch("fluidize.adapters.local.projects.ProjectProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            yield mock_processor

    @pytest.fixture
    def projects_handler(self, mock_config, mock_processor):
        """Create a ProjectsHandler instance for testing."""
        return ProjectsHandler(mock_config)

    def test_init(self, mock_config):
        """Test ProjectsHandler initialization."""
        handler = ProjectsHandler(mock_config)

        assert handler.config == mock_config
        assert handler.processor is not None

    def test_delete_success(self, projects_handler, mock_processor):
        """Test successful project deletion."""
        project_id = "test-project-001"

        result = projects_handler.delete(project_id)

        mock_processor.delete_project.assert_called_once_with(project_id)
        assert result == {"success": True, "message": f"Project {project_id} deleted"}

    def test_delete_with_processor_error(self, projects_handler, mock_processor):
        """Test delete when processor raises an error."""
        project_id = "non-existent-project"
        mock_processor.delete_project.side_effect = FileNotFoundError("Project not found")

        with pytest.raises(FileNotFoundError):
            projects_handler.delete(project_id)

        mock_processor.delete_project.assert_called_once_with(project_id)

    def test_list_empty(self, projects_handler, mock_processor):
        """Test list projects when no projects exist."""
        mock_processor.get_projects.return_value = []

        result = projects_handler.list()

        assert result == []
        mock_processor.get_projects.assert_called_once()

    def test_list_with_projects(self, projects_handler, mock_processor):
        """Test list projects with multiple projects."""
        sample_projects = SampleProjects.projects_for_listing()
        mock_processor.get_projects.return_value = sample_projects

        result = projects_handler.list()

        assert result == sample_projects
        assert len(result) == 3
        assert all(isinstance(p, ProjectSummary) for p in result)
        mock_processor.get_projects.assert_called_once()

    def test_retrieve_success(self, projects_handler, mock_processor):
        """Test successful project retrieval."""
        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id
        mock_processor.get_project.return_value = sample_project

        result = projects_handler.retrieve(project_id)

        assert result == sample_project
        mock_processor.get_project.assert_called_once_with(project_id)

    def test_retrieve_not_found(self, projects_handler, mock_processor):
        """Test retrieve when project doesn't exist."""
        project_id = "non-existent"
        mock_processor.get_project.side_effect = FileNotFoundError("Project not found")

        with pytest.raises(FileNotFoundError):
            projects_handler.retrieve(project_id)

        mock_processor.get_project.assert_called_once_with(project_id)

    def test_upsert_with_all_fields(self, projects_handler, mock_processor):
        """Test upsert with all optional fields provided."""
        sample_project = SampleProjects.standard_project()
        mock_processor.upsert_project.return_value = sample_project

        project_data = {
            "id": sample_project.id,
            "description": sample_project.description,
            "label": sample_project.label,
            "location": sample_project.location,
            "metadata_version": sample_project.metadata_version,
            "status": sample_project.status,
        }

        result = projects_handler.upsert(**project_data)

        assert result == sample_project
        mock_processor.upsert_project.assert_called_once_with(**project_data)

    def test_upsert_minimal_fields(self, projects_handler, mock_processor):
        """Test upsert with only required fields."""
        minimal_project = SampleProjects.minimal_project()
        mock_processor.upsert_project.return_value = minimal_project

        result = projects_handler.upsert(id=minimal_project.id)

        assert result == minimal_project
        mock_processor.upsert_project.assert_called_once_with(
            id=minimal_project.id, description=None, label=None, location=None, metadata_version="1.0", status=None
        )

    def test_upsert_with_kwargs(self, projects_handler, mock_processor):
        """Test upsert passes through additional kwargs."""
        sample_project = SampleProjects.standard_project()
        mock_processor.upsert_project.return_value = sample_project

        extra_kwargs = {"custom_field": "custom_value", "another_field": "another_value"}

        result = projects_handler.upsert(id=sample_project.id, label=sample_project.label, **extra_kwargs)

        assert result == sample_project
        expected_call = {
            "id": sample_project.id,
            "description": None,
            "label": sample_project.label,
            "location": None,
            "metadata_version": "1.0",
            "status": None,
            **extra_kwargs,
        }
        mock_processor.upsert_project.assert_called_once_with(**expected_call)

    @pytest.mark.parametrize(
        "field_name,field_value",
        [
            ("description", "Test description"),
            ("label", "Test Label"),
            ("location", "/test/location"),
            ("status", "active"),
            ("metadata_version", "2.0"),
        ],
    )
    def test_upsert_individual_fields(self, projects_handler, mock_processor, field_name, field_value):
        """Test upsert with individual optional fields."""
        sample_project = SampleProjects.standard_project()
        mock_processor.upsert_project.return_value = sample_project

        kwargs = {"id": "test-project", field_name: field_value}

        result = projects_handler.upsert(**kwargs)

        assert result == sample_project

        # Build expected call arguments
        expected_kwargs = {
            "id": "test-project",
            "description": None,
            "label": None,
            "location": None,
            "metadata_version": "1.0",
            "status": None,
        }
        expected_kwargs[field_name] = field_value

        mock_processor.upsert_project.assert_called_once_with(**expected_kwargs)

    def test_upsert_overrides_default_metadata_version(self, projects_handler, mock_processor):
        """Test upsert can override default metadata version."""
        sample_project = SampleProjects.standard_project()
        mock_processor.upsert_project.return_value = sample_project

        result = projects_handler.upsert(id="version-test", metadata_version="2.0")

        assert result == sample_project
        mock_processor.upsert_project.assert_called_once_with(
            id="version-test", description=None, label=None, location=None, metadata_version="2.0", status=None
        )

    def test_upsert_none_values_preserved(self, projects_handler, mock_processor):
        """Test that explicitly passed None values are preserved in upsert."""
        sample_project = SampleProjects.standard_project()
        mock_processor.upsert_project.return_value = sample_project

        result = projects_handler.upsert(
            id="none-test", description=None, label="Actual Label", location=None, status=None
        )

        assert result == sample_project
        mock_processor.upsert_project.assert_called_once_with(
            id="none-test", description=None, label="Actual Label", location=None, metadata_version="1.0", status=None
        )

    def test_processor_error_propagation(self, projects_handler, mock_processor):
        """Test that processor errors are properly propagated."""
        # Test for list operation
        mock_processor.get_projects.side_effect = RuntimeError("Database error")

        with pytest.raises(RuntimeError, match="Database error"):
            projects_handler.list()

        # Test for upsert operation
        mock_processor.upsert_project.side_effect = ValueError("Invalid data")

        with pytest.raises(ValueError, match="Invalid data"):
            projects_handler.upsert(id="error-test")

    def test_config_passed_to_processor(self, mock_config):
        """Test that config is properly stored and available."""
        handler = ProjectsHandler(mock_config)

        assert handler.config == mock_config
        # The processor itself doesn't use config in the current implementation,
        # but the handler should store it for potential future use
