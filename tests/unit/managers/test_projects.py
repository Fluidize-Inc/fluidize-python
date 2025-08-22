"""Unit tests for Projects Manager - high-level project management interface."""

from unittest.mock import Mock

import pytest

from fluidize.core.utils.exceptions import ProjectAlreadyExistsError
from fluidize.managers.registry import RegistryManager
from tests.fixtures.sample_projects import SampleProjects


class TestProjectsManager:
    """Test suite for Projects manager class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter with projects handler."""
        adapter = Mock()
        adapter.projects = Mock()
        return adapter

    @pytest.fixture
    def projects_manager(self, mock_adapter):
        """Create a Projects manager instance for testing."""
        return RegistryManager(mock_adapter)

    def test_init(self, mock_adapter):
        """Test Projects manager initialization."""
        manager = RegistryManager(mock_adapter)

        assert manager.adapter is mock_adapter

    def test_create_project_with_all_fields(self, projects_manager, mock_adapter):
        """Test create method with all optional fields."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        mock_adapter.projects.upsert.return_value = sample_project
        # Mock retrieve to raise FileNotFoundError (project doesn't exist yet)
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        result = projects_manager.create(
            project_id=sample_project.id,
            label=sample_project.label,
            description=sample_project.description,
            location=sample_project.location,
            status=sample_project.status,
        )

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        assert result.label == sample_project.label
        assert result.description == sample_project.description
        assert result.location == sample_project.location
        assert result.status == sample_project.status
        mock_adapter.projects.upsert.assert_called_once_with(
            id=sample_project.id,
            label=sample_project.label,
            description=sample_project.description,
            location=sample_project.location,
            status=sample_project.status,
        )

    def test_create_project_minimal(self, projects_manager, mock_adapter):
        """Test create method with minimal required fields."""
        from fluidize.managers.project import ProjectManager

        project_id = "minimal-create"
        minimal_project = SampleProjects.minimal_project()
        mock_adapter.projects.upsert.return_value = minimal_project
        # Mock retrieve to raise FileNotFoundError (project doesn't exist yet)
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        result = projects_manager.create(project_id)

        assert isinstance(result, ProjectManager)
        assert result.id == minimal_project.id
        assert result.metadata_version == minimal_project.metadata_version
        mock_adapter.projects.upsert.assert_called_once_with(
            id=project_id, label="", description="", location="", status=""
        )

    def test_create_project_partial_fields(self, projects_manager, mock_adapter):
        """Test create method with some optional fields."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        mock_adapter.projects.upsert.return_value = sample_project
        # Mock retrieve to raise FileNotFoundError (project doesn't exist yet)
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        result = projects_manager.create(
            project_id="partial-create", label="Partial Project", description="Only some fields provided"
        )

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        mock_adapter.projects.upsert.assert_called_once_with(
            id="partial-create",
            label="Partial Project",
            description="Only some fields provided",
            location="",
            status="",
        )

    def test_get_project(self, projects_manager, mock_adapter):
        """Test get method retrieves project by ID."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id
        mock_adapter.projects.retrieve.return_value = sample_project

        result = projects_manager.get(project_id)

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        mock_adapter.projects.retrieve.assert_called_once_with(project_id)

    def test_get_project_not_found(self, projects_manager, mock_adapter):
        """Test get method propagates adapter errors."""
        project_id = "non-existent"
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        with pytest.raises(FileNotFoundError):
            projects_manager.get(project_id)

        mock_adapter.projects.retrieve.assert_called_once_with(project_id)

    def test_create_project_already_exists(self, projects_manager, mock_adapter):
        """Test create method raises error when project already exists."""
        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id

        # Mock get to return existing project (no FileNotFoundError)
        mock_adapter.projects.retrieve.return_value = sample_project

        with pytest.raises(ProjectAlreadyExistsError) as exc_info:
            projects_manager.create(project_id, label="New Label")

        # Verify error message contains project ID
        assert project_id in str(exc_info.value)
        assert exc_info.value.project_id == project_id

        # Verify retrieve was called but upsert was not
        mock_adapter.projects.retrieve.assert_called_once_with(project_id)
        mock_adapter.projects.upsert.assert_not_called()

    def test_list_projects_empty(self, projects_manager, mock_adapter):
        """Test list method when no projects exist."""
        mock_adapter.projects.list.return_value = []

        result = projects_manager.list()

        assert result == []
        mock_adapter.projects.list.assert_called_once()

    def test_list_projects_with_data(self, projects_manager, mock_adapter):
        """Test list method with multiple projects."""
        from fluidize.managers.project import ProjectManager

        sample_projects = SampleProjects.projects_for_listing()
        mock_adapter.projects.list.return_value = sample_projects

        result = projects_manager.list()

        assert isinstance(result, list)
        assert len(result) == 3
        for project in result:
            assert isinstance(project, ProjectManager)
        mock_adapter.projects.list.assert_called_once()

    def test_update_project_with_all_fields(self, projects_manager, mock_adapter):
        """Test update method with all optional fields."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id
        mock_adapter.projects.upsert.return_value = sample_project

        update_data = SampleProjects.project_update_data()

        result = projects_manager.update(
            project_id=project_id,
            label=update_data["label"],
            description=update_data["description"],
            location=update_data["location"],
            status=update_data["status"],
        )

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        mock_adapter.projects.upsert.assert_called_once_with(
            id=project_id,
            label=update_data["label"],
            description=update_data["description"],
            location=update_data["location"],
            status=update_data["status"],
        )

    def test_update_project_partial_fields(self, projects_manager, mock_adapter):
        """Test update method with only some fields."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        project_id = "update-partial"
        mock_adapter.projects.upsert.return_value = sample_project

        result = projects_manager.update(
            project_id=project_id, label="Updated Label", description="Updated Description"
        )

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        mock_adapter.projects.upsert.assert_called_once_with(
            id=project_id, label="Updated Label", description="Updated Description"
        )

    def test_update_project_no_optional_fields(self, projects_manager, mock_adapter):
        """Test update method with only project_id."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        project_id = "update-id-only"
        mock_adapter.projects.upsert.return_value = sample_project

        result = projects_manager.update(project_id=project_id)

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        mock_adapter.projects.upsert.assert_called_once_with(id=project_id)

    @pytest.mark.parametrize(
        "field_name,field_value",
        [
            ("label", "Single Label Update"),
            ("description", "Single Description Update"),
            ("location", "/single/location/update"),
            ("status", "single-status-update"),
        ],
    )
    def test_update_project_single_field(self, projects_manager, mock_adapter, field_name, field_value):
        """Test update method with individual fields."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        project_id = "single-field-update"
        mock_adapter.projects.upsert.return_value = sample_project

        kwargs = {"project_id": project_id, field_name: field_value}

        result = projects_manager.update(**kwargs)

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id

        expected_call = {"id": project_id, field_name: field_value}
        mock_adapter.projects.upsert.assert_called_once_with(**expected_call)

    def test_update_filters_none_values(self, projects_manager, mock_adapter):
        """Test update method only includes non-None values in update data."""
        from fluidize.managers.project import ProjectManager

        sample_project = SampleProjects.standard_project()
        project_id = "filter-none-test"
        mock_adapter.projects.upsert.return_value = sample_project

        result = projects_manager.update(
            project_id=project_id,
            label="New Label",
            description=None,  # Should be filtered out
            location="/new/location",
            status=None,  # Should be filtered out
        )

        assert isinstance(result, ProjectManager)
        assert result.id == sample_project.id
        mock_adapter.projects.upsert.assert_called_once_with(
            id=project_id,
            label="New Label",
            location="/new/location",
            # Note: description and status should not be in the call
        )

    def test_adapter_error_propagation(self, projects_manager, mock_adapter):
        """Test that adapter errors are properly propagated through manager methods."""
        # Test create error - first mock retrieve to return FileNotFoundError (project doesn't exist)
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")
        mock_adapter.projects.upsert.side_effect = ValueError("Invalid project data")

        with pytest.raises(ValueError, match="Invalid project data"):
            projects_manager.create("error-test")

        # Test get error
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")

        with pytest.raises(FileNotFoundError, match="Project not found"):
            projects_manager.get("missing-project")

        # Test list error
        mock_adapter.projects.list.side_effect = RuntimeError("Database error")

        with pytest.raises(RuntimeError, match="Database error"):
            projects_manager.list()

    def test_manager_adapter_delegation(self, mock_adapter):
        """Test that manager properly delegates to adapter methods."""
        manager = RegistryManager(mock_adapter)

        # Ensure manager stores adapter correctly
        assert manager.adapter is mock_adapter

        # Test all methods delegate to adapter.projects
        test_project = SampleProjects.standard_project()
        mock_adapter.projects.upsert.return_value = test_project
        mock_adapter.projects.retrieve.return_value = test_project
        mock_adapter.projects.list.return_value = [test_project]

        # Call all manager methods
        # Mock retrieve to raise FileNotFoundError (project doesn't exist yet)
        mock_adapter.projects.retrieve.side_effect = [
            FileNotFoundError("Project not found"),
            test_project,
            test_project,
        ]
        manager.create("test-create")
        manager.get("test-get")
        manager.list()
        manager.update("test-update", label="Updated")

        # Verify adapter was called
        assert mock_adapter.projects.upsert.call_count == 2  # create + update
        assert mock_adapter.projects.retrieve.call_count == 2  # create (check if exists) + get
        mock_adapter.projects.list.assert_called_once()

    def test_manager_interface_compatibility(self, mock_adapter):
        """Test that manager provides expected interface methods."""
        manager = RegistryManager(mock_adapter)

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

    def test_project_wrapper_return_types(self, mock_adapter):
        """Test that manager methods return Project wrapper instances."""
        from fluidize.managers.project import ProjectManager

        manager = RegistryManager(mock_adapter)
        sample_project = SampleProjects.standard_project()
        mock_adapter.projects.upsert.return_value = sample_project
        mock_adapter.projects.retrieve.return_value = sample_project
        mock_adapter.projects.list.return_value = [sample_project]

        # Test create returns Project wrapper
        # Mock retrieve to raise FileNotFoundError for create (project doesn't exist yet)
        mock_adapter.projects.retrieve.side_effect = [
            FileNotFoundError("Project not found"),
            sample_project,
            sample_project,
        ]
        created_project = manager.create("test-create")
        assert isinstance(created_project, ProjectManager)
        assert created_project.id == sample_project.id

        # Test get returns Project wrapper
        retrieved_project = manager.get("test-get")
        assert isinstance(retrieved_project, ProjectManager)
        assert retrieved_project.id == sample_project.id

        # Test list returns list of Project wrappers
        projects_list = manager.list()
        assert isinstance(projects_list, list)
        assert len(projects_list) == 1
        assert isinstance(projects_list[0], ProjectManager)
        assert projects_list[0].id == sample_project.id

        # Test update returns Project wrapper
        updated_project = manager.update("test-update", label="New Label")
        assert isinstance(updated_project, ProjectManager)
        assert updated_project.id == sample_project.id

    def test_project_wrapper_graph_property_access(self, mock_adapter):
        """Test that Project wrapper provides graph property access."""

        manager = RegistryManager(mock_adapter)
        sample_project = SampleProjects.standard_project()
        mock_adapter.projects.upsert.return_value = sample_project
        mock_adapter.graph = Mock()  # Mock graph handler

        # Mock retrieve to raise FileNotFoundError (project doesn't exist yet)
        mock_adapter.projects.retrieve.side_effect = FileNotFoundError("Project not found")
        project = manager.create("test-graph-access")

        # Verify project has graph property
        assert hasattr(project, "graph")

        # Accessing graph should not raise error
        graph = project.graph
        assert graph is not None
