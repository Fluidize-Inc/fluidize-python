"""Unit tests for ProjectProcessor - the core business logic for project operations."""

from unittest.mock import Mock, call, patch

import pytest
from upath import UPath

from fluidize.core.constants import FileConstants
from fluidize.core.modules.projects.processor import ProjectProcessor
from fluidize.core.types.project import ProjectSummary
from tests.fixtures.sample_projects import SampleProjects


class TestProjectProcessor:
    """Test suite for ProjectProcessor class."""

    def test_init(self):
        """Test ProjectProcessor initialization."""
        processor = ProjectProcessor()
        assert processor is not None

    def test_get_projects_empty_directory(self, mock_path_finder: Mock, mock_data_loader: Mock):
        """Test get_projects when projects directory doesn't exist."""
        processor = ProjectProcessor()

        # Mock empty projects directory that doesn't exist
        mock_projects_path = Mock(spec=UPath)
        mock_projects_path.exists.return_value = False
        mock_path_finder.get_projects_path.return_value = mock_projects_path

        result = processor.get_projects()

        assert result == []
        mock_path_finder.get_projects_path.assert_called_once()
        mock_projects_path.exists.assert_called_once()

    def test_get_projects_with_valid_projects(self, mock_path_finder: Mock, mock_data_loader: Mock):
        """Test get_projects with valid project directories."""
        processor = ProjectProcessor()
        sample_projects = SampleProjects.projects_for_listing()

        # Mock directory structure
        mock_projects_path = Mock(spec=UPath)
        mock_projects_path.exists.return_value = True
        mock_project_dirs = [UPath(f"/fake/projects/{p.id}") for p in sample_projects]

        mock_path_finder.get_projects_path.return_value = mock_projects_path
        mock_data_loader.list_directories.return_value = mock_project_dirs

        # Mock ProjectSummary.from_file to return our sample projects
        with patch.object(ProjectSummary, "from_file") as mock_from_file:
            mock_from_file.side_effect = sample_projects

            result = processor.get_projects()

        assert len(result) == 3
        assert all(isinstance(p, ProjectSummary) for p in result)
        assert result == sample_projects

        # Verify calls
        mock_path_finder.get_projects_path.assert_called_once()
        mock_projects_path.exists.assert_called_once()
        mock_data_loader.list_directories.assert_called_once_with(mock_projects_path)
        assert mock_from_file.call_count == 3

    def test_get_projects_skips_invalid_directories(self, mock_path_finder: Mock, mock_data_loader: Mock):
        """Test get_projects skips directories without valid project metadata."""
        processor = ProjectProcessor()

        # Mock directory structure with some invalid directories
        mock_projects_path = Mock(spec=UPath)
        mock_projects_path.exists.return_value = True
        mock_project_dirs = [
            UPath("/fake/projects/valid-project"),
            UPath("/fake/projects/invalid-project"),
            UPath("/fake/projects/another-valid"),
        ]

        mock_path_finder.get_projects_path.return_value = mock_projects_path
        mock_data_loader.list_directories.return_value = mock_project_dirs

        # Mock ProjectSummary.from_file to raise exceptions for invalid projects
        valid_project = SampleProjects.standard_project()
        with patch.object(ProjectSummary, "from_file") as mock_from_file:
            mock_from_file.side_effect = [
                valid_project,  # valid-project
                FileNotFoundError(),  # invalid-project
                valid_project,  # another-valid
            ]

            result = processor.get_projects()

        assert len(result) == 2
        assert all(p == valid_project for p in result)

    def test_get_project_success(self, mock_path_finder: Mock, mock_data_loader: Mock):
        """Test get_project successfully retrieves a project."""
        processor = ProjectProcessor()
        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id

        # Mock paths
        mock_projects_path = UPath("/fake/projects")
        mock_project_path = mock_projects_path / project_id

        mock_path_finder.get_projects_path.return_value = mock_projects_path

        with patch.object(ProjectSummary, "from_file") as mock_from_file:
            mock_from_file.return_value = sample_project

            result = processor.get_project(project_id)

        assert result == sample_project
        mock_path_finder.get_projects_path.assert_called_once()
        mock_from_file.assert_called_once_with(mock_project_path)

    def test_get_project_not_found(self, mock_path_finder: Mock, mock_data_loader: Mock):
        """Test get_project raises FileNotFoundError when project doesn't exist."""
        processor = ProjectProcessor()
        project_id = "non-existent-project"

        mock_projects_path = UPath("/fake/projects")
        mock_project_path = mock_projects_path / project_id

        mock_path_finder.get_projects_path.return_value = mock_projects_path

        with patch.object(ProjectSummary, "from_file") as mock_from_file:
            mock_from_file.side_effect = FileNotFoundError()

            with pytest.raises(FileNotFoundError):
                processor.get_project(project_id)

        mock_from_file.assert_called_once_with(mock_project_path)

    def test_create_new_project(self, mock_path_finder: Mock, mock_data_writer: Mock):
        """Test _create_new_project creates filesystem structure."""
        processor = ProjectProcessor()
        sample_project = SampleProjects.standard_project()

        mock_project_path = UPath(f"/fake/projects/{sample_project.id}")
        mock_metadata_path = mock_project_path / FileConstants.METADATA_SUFFIX

        mock_path_finder.get_project_path.return_value = mock_project_path

        with patch("fluidize.core.modules.projects.processor.DataWriter", mock_data_writer):
            processor._create_new_project(sample_project)

        # Verify the correct files are written
        expected_calls = [
            call.write_json_for_project(
                sample_project, FileConstants.PARAMETERS_SUFFIX, {"metadata": {}, "parameters": {}}
            ),
            call.write_json_for_project(sample_project, FileConstants.GRAPH_SUFFIX, {"nodes": [], "edges": []}),
            call.write_yaml(mock_metadata_path, {"project": sample_project.model_dump()}),
        ]

        mock_data_writer.assert_has_calls(expected_calls, any_order=True)

    def test_insert_project_new_project(self, mock_path_finder: Mock, mock_data_writer: Mock):
        """Test insert_project creates new project when it doesn't exist."""
        processor = ProjectProcessor()
        sample_project = SampleProjects.standard_project()

        mock_projects_path = UPath("/fake/projects")
        mock_project_path = mock_projects_path / sample_project.id

        mock_path_finder.get_projects_path.return_value = mock_projects_path
        mock_path_finder.get_project_path.return_value = mock_project_path

        with patch.object(processor, "get_project") as mock_get_project:
            mock_get_project.side_effect = FileNotFoundError()

            with patch("fluidize.core.modules.projects.processor.DataWriter", mock_data_writer):
                result = processor.insert_project(sample_project)

        assert result == sample_project
        mock_get_project.assert_called_once_with(sample_project.id)
        # Verify creation was called (via DataWriter calls)
        assert mock_data_writer.write_json_for_project.called
        assert mock_data_writer.write_yaml.called

    def test_insert_project_update_existing(self, mock_path_finder: Mock, mock_data_writer: Mock):
        """Test insert_project updates existing project."""
        processor = ProjectProcessor()
        sample_project = SampleProjects.standard_project()

        mock_project_path = UPath(f"/fake/projects/{sample_project.id}")
        mock_metadata_path = mock_project_path / FileConstants.METADATA_SUFFIX

        mock_path_finder.get_project_path.return_value = mock_project_path

        with patch.object(processor, "get_project") as mock_get_project:
            mock_get_project.return_value = sample_project  # Project exists

            with patch("fluidize.core.modules.projects.processor.DataWriter", mock_data_writer):
                result = processor.insert_project(sample_project)

        assert result == sample_project
        mock_get_project.assert_called_once_with(sample_project.id)
        # Verify update was called (metadata write)
        mock_data_writer.write_yaml.assert_called_with(mock_metadata_path, {"project": sample_project.model_dump()})

    def test_update_project_metadata(self, mock_path_finder: Mock, mock_data_writer: Mock):
        """Test _update_project_metadata writes updated metadata."""
        processor = ProjectProcessor()
        sample_project = SampleProjects.standard_project()

        mock_project_path = UPath(f"/fake/projects/{sample_project.id}")
        mock_metadata_path = mock_project_path / FileConstants.METADATA_SUFFIX

        mock_path_finder.get_project_path.return_value = mock_project_path

        with patch("fluidize.core.modules.projects.processor.DataWriter", mock_data_writer):
            processor._update_project_metadata(sample_project)

        mock_data_writer.write_yaml.assert_called_once_with(
            mock_metadata_path, {"project": sample_project.model_dump()}
        )

    def test_delete_project_success(self, mock_data_loader: Mock):
        """Test delete_project removes project successfully."""
        processor = ProjectProcessor()
        sample_project = SampleProjects.standard_project()
        project_id = sample_project.id

        with patch.object(processor, "get_project") as mock_get_project:
            mock_get_project.return_value = sample_project

            processor.delete_project(project_id)

        mock_get_project.assert_called_once_with(project_id)
        mock_data_loader.delete_entire_project_folder.assert_called_once_with(sample_project)

    def test_delete_project_not_found(self):
        """Test delete_project raises error when project doesn't exist."""
        processor = ProjectProcessor()
        project_id = "non-existent"

        with patch.object(processor, "get_project") as mock_get_project:
            mock_get_project.side_effect = FileNotFoundError()

            with pytest.raises(FileNotFoundError):
                processor.delete_project(project_id)

    def test_upsert_project_with_all_fields(self):
        """Test upsert_project with all optional fields provided."""
        processor = ProjectProcessor()

        project_data = {
            "id": "upsert-test",
            "description": "Test description",
            "label": "Test Label",
            "location": "/test/location",
            "metadata_version": "1.0",
            "status": "active",
        }

        with patch.object(processor, "insert_project") as mock_insert:
            expected_project = ProjectSummary(**project_data)
            mock_insert.return_value = expected_project

            result = processor.upsert_project(**project_data)

        assert result == expected_project
        mock_insert.assert_called_once()
        # Verify the ProjectSummary was created with correct data
        created_project = mock_insert.call_args[0][0]
        assert created_project.id == project_data["id"]
        assert created_project.description == project_data["description"]
        assert created_project.label == project_data["label"]

    def test_upsert_project_minimal_fields(self):
        """Test upsert_project with only required fields."""
        processor = ProjectProcessor()

        with patch.object(processor, "insert_project") as mock_insert:
            expected_project = ProjectSummary(id="minimal-test", metadata_version="1.0")
            mock_insert.return_value = expected_project

            result = processor.upsert_project(id="minimal-test")

        assert result == expected_project
        created_project = mock_insert.call_args[0][0]
        assert created_project.id == "minimal-test"
        assert created_project.metadata_version == "1.0"
        assert created_project.label == ""  # Default empty values

    def test_upsert_project_filters_non_string_kwargs(self):
        """Test upsert_project filters out non-string kwargs."""
        processor = ProjectProcessor()

        with patch.object(processor, "insert_project") as mock_insert:
            processor.upsert_project(
                id="kwargs-test",
                label="Test Label",
                invalid_int=123,  # Should be filtered out
                invalid_list=["a", "b"],  # Should be filtered out
                valid_string="valid",  # Should be included
            )

            created_project = mock_insert.call_args[0][0]
            assert created_project.id == "kwargs-test"
            assert created_project.label == "Test Label"
            # Non-string kwargs should not be in the model
            assert not hasattr(created_project, "invalid_int")
            assert not hasattr(created_project, "invalid_list")

    @pytest.mark.parametrize(
        "field_name,field_value",
        [
            ("description", "Updated description"),
            ("label", "Updated label"),
            ("location", "/updated/location"),
            ("status", "updated"),
        ],
    )
    def test_upsert_project_individual_fields(self, field_name: str, field_value: str):
        """Test upsert_project with individual optional fields."""
        processor = ProjectProcessor()

        kwargs = {"id": "field-test", field_name: field_value}

        with patch.object(processor, "insert_project") as mock_insert:
            processor.upsert_project(**kwargs)

            created_project = mock_insert.call_args[0][0]
            assert getattr(created_project, field_name) == field_value
