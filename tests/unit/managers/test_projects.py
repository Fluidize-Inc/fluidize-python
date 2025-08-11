"""Unit tests for Projects Manager - high-level project management interface."""

from unittest.mock import Mock

import pytest

from fluidize.managers.projects import Projects
from tests.fixtures.sample_projects import SampleProjects


class TestProjectsManager:
    """Test suite for Projects manager class."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend with projects handler."""
        backend = Mock()
        backend.projects = Mock()
        return backend

    @pytest.fixture
    def projects_manager(self, mock_backend):
        """Create a Projects manager instance for testing."""
        return Projects(mock_backend)

    def test_init(self, mock_backend):
        """Test Projects manager initialization."""
        manager = Projects(mock_backend)

        assert manager.backend is mock_backend

    def test_create_project_with_all_fields(self, projects_manager, mock_backend):
        """Test create method with all optional fields."""
        sample_project = SampleProjects.standard_project()
        mock_backend.projects.upsert.return_value = sample_project

        result = projects_manager.create(
            project_id=sample_project.id,
            label=sample_project.label,
            description=sample_project.description,
            location=sample_project.location,
            status=sample_project.status,
        )

        assert result == sample_project
        mock_backend.projects.upsert.assert_called_once_with(
            id=sample_project.id,
            label=sample_project.label,
            description=sample_project.description,
            location=sample_project.location,
            status=sample_project.status,
        )

    def test_create_project_minimal(self, projects_manager, mock_backend):
        """Test create method with minimal required fields."""
        project_id = "minimal-create"
        minimal_project = SampleProjects.minimal_project()
        mock_backend.projects.upsert.return_value = minimal_project

        result = projects_manager.create(project_id)

        assert result == minimal_project
        mock_backend.projects.upsert.assert_called_once_with(
            id=project_id, label="", description="", location="", status=""
        )

    def test_create_project_partial_fields(self, projects_manager, mock_backend):
        """Test create method with some optional fields."""
        sample_project = SampleProjects.standard_project()
        mock_backend.projects.upsert.return_value = sample_project

        result = projects_manager.create(
            project_id="partial-create", label="Partial Project", description="Only some fields provided"
        )

        assert result == sample_project
        mock_backend.projects.upsert.assert_called_once_with(
            id="partial-create",
            label="Partial Project",
            description="Only some fields provided",
            location="",
            status="",
        )

    def test_get_project(self, projects_manager, mock_backend):
        """Test get method retrieves project by ID."""
        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id
        mock_backend.projects.retrieve.return_value = sample_project

        result = projects_manager.get(project_id)

        assert result == sample_project
        mock_backend.projects.retrieve.assert_called_once_with(project_id)

    def test_get_project_not_found(self, projects_manager, mock_backend):
        """Test get method propagates backend errors."""
        project_id = "non-existent"
        mock_backend.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        with pytest.raises(FileNotFoundError):
            projects_manager.get(project_id)

        mock_backend.projects.retrieve.assert_called_once_with(project_id)

    def test_list_projects_empty(self, projects_manager, mock_backend):
        """Test list method when no projects exist."""
        mock_backend.projects.list.return_value = []

        result = projects_manager.list()

        assert result == []
        mock_backend.projects.list.assert_called_once()

    def test_list_projects_with_data(self, projects_manager, mock_backend):
        """Test list method with multiple projects."""
        sample_projects = SampleProjects.projects_for_listing()
        mock_backend.projects.list.return_value = sample_projects

        result = projects_manager.list()

        assert result == sample_projects
        assert len(result) == 3
        mock_backend.projects.list.assert_called_once()

    def test_update_project_with_all_fields(self, projects_manager, mock_backend):
        """Test update method with all optional fields."""
        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id
        mock_backend.projects.upsert.return_value = sample_project

        update_data = SampleProjects.project_update_data()

        result = projects_manager.update(
            project_id=project_id,
            label=update_data["label"],
            description=update_data["description"],
            location=update_data["location"],
            status=update_data["status"],
        )

        assert result == sample_project
        mock_backend.projects.upsert.assert_called_once_with(
            id=project_id,
            label=update_data["label"],
            description=update_data["description"],
            location=update_data["location"],
            status=update_data["status"],
        )

    def test_update_project_partial_fields(self, projects_manager, mock_backend):
        """Test update method with only some fields."""
        sample_project = SampleProjects.standard_project()
        project_id = "update-partial"
        mock_backend.projects.upsert.return_value = sample_project

        result = projects_manager.update(
            project_id=project_id, label="Updated Label", description="Updated Description"
        )

        assert result == sample_project
        mock_backend.projects.upsert.assert_called_once_with(
            id=project_id, label="Updated Label", description="Updated Description"
        )

    def test_update_project_no_optional_fields(self, projects_manager, mock_backend):
        """Test update method with only project_id."""
        sample_project = SampleProjects.standard_project()
        project_id = "update-id-only"
        mock_backend.projects.upsert.return_value = sample_project

        result = projects_manager.update(project_id=project_id)

        assert result == sample_project
        mock_backend.projects.upsert.assert_called_once_with(id=project_id)

    @pytest.mark.parametrize(
        "field_name,field_value",
        [
            ("label", "Single Label Update"),
            ("description", "Single Description Update"),
            ("location", "/single/location/update"),
            ("status", "single-status-update"),
        ],
    )
    def test_update_project_single_field(self, projects_manager, mock_backend, field_name, field_value):
        """Test update method with individual fields."""
        sample_project = SampleProjects.standard_project()
        project_id = "single-field-update"
        mock_backend.projects.upsert.return_value = sample_project

        kwargs = {"project_id": project_id, field_name: field_value}

        result = projects_manager.update(**kwargs)

        assert result == sample_project

        expected_call = {"id": project_id, field_name: field_value}
        mock_backend.projects.upsert.assert_called_once_with(**expected_call)

    def test_update_filters_none_values(self, projects_manager, mock_backend):
        """Test update method only includes non-None values in update data."""
        sample_project = SampleProjects.standard_project()
        project_id = "filter-none-test"
        mock_backend.projects.upsert.return_value = sample_project

        result = projects_manager.update(
            project_id=project_id,
            label="New Label",
            description=None,  # Should be filtered out
            location="/new/location",
            status=None,  # Should be filtered out
        )

        assert result == sample_project
        mock_backend.projects.upsert.assert_called_once_with(
            id=project_id,
            label="New Label",
            location="/new/location",
            # Note: description and status should not be in the call
        )

    def test_backend_error_propagation(self, projects_manager, mock_backend):
        """Test that backend errors are properly propagated through manager methods."""
        # Test create error
        mock_backend.projects.upsert.side_effect = ValueError("Invalid project data")

        with pytest.raises(ValueError, match="Invalid project data"):
            projects_manager.create("error-test")

        # Test get error
        mock_backend.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        with pytest.raises(FileNotFoundError, match="Project not found"):
            projects_manager.get("missing-project")

        # Test list error
        mock_backend.projects.list.side_effect = RuntimeError("Database error")

        with pytest.raises(RuntimeError, match="Database error"):
            projects_manager.list()

    def test_manager_backend_delegation(self, mock_backend):
        """Test that manager properly delegates to backend methods."""
        manager = Projects(mock_backend)

        # Ensure manager stores backend correctly
        assert manager.backend is mock_backend

        # Test all methods delegate to backend.projects
        test_project = SampleProjects.standard_project()
        mock_backend.projects.upsert.return_value = test_project
        mock_backend.projects.retrieve.return_value = test_project
        mock_backend.projects.list.return_value = [test_project]

        # Call all manager methods
        manager.create("test-create")
        manager.get("test-get")
        manager.list()
        manager.update("test-update", label="Updated")

        # Verify backend was called
        assert mock_backend.projects.upsert.call_count == 2  # create + update
        mock_backend.projects.retrieve.assert_called_once()
        mock_backend.projects.list.assert_called_once()

    def test_manager_interface_compatibility(self, mock_backend):
        """Test that manager provides expected interface methods."""
        manager = Projects(mock_backend)

        # Verify all expected methods exist
        assert hasattr(manager, "create")
        assert hasattr(manager, "get")
        assert hasattr(manager, "list")
        assert hasattr(manager, "update")

        # Verify methods are callable
        assert callable(manager.create)
        assert callable(manager.get)
        assert callable(manager.list)
        assert callable(manager.update)
