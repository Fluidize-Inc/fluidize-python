"""
Local filesystem-based project processor.

This module provides the core business logic for project operations using
the local filesystem, without any cloud or Firebase dependencies.
"""

from typing import Optional

from fluidize.core.constants import FileConstants
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.dataloader.data_loader import DataLoader
from fluidize.core.utils.dataloader.data_writer import DataWriter
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class ProjectProcessor:
    """
    Local filesystem-based project processor.

    Handles all project operations using the filesystem as the source of truth,
    compatible with the FastAPI interface but without cloud dependencies.
    """

    def __init__(self) -> None:
        """
        Initialize the project processor.
        No user_id needed - local filesystem doesn't have user concepts.
        """
        pass

    def _create_new_project(self, project: ProjectSummary) -> None:
        """
        Create the filesystem structure for a new project.

        Args:
            project: The project to create
        """
        project_path = PathFinder.get_project_path(project)

        # Create empty graph and parameters files
        empty_graph: dict[str, list] = {"nodes": [], "edges": []}
        empty_params: dict[str, dict] = {"metadata": {}, "parameters": {}}

        # Write initial files
        DataWriter.write_json_for_project(project, FileConstants.PARAMETERS_SUFFIX, empty_params)
        DataWriter.write_json_for_project(project, FileConstants.GRAPH_SUFFIX, empty_graph)

        # Write project metadata
        metadata_path = project_path / FileConstants.METADATA_SUFFIX
        project_data = {"project": project.model_dump()}
        DataWriter.write_yaml(metadata_path, project_data)

    def get_projects(self) -> list[ProjectSummary]:
        """
        Get all projects by scanning the filesystem.

        Returns:
            List of all projects found in the projects directory
        """
        projects = []
        projects_path = PathFinder.get_projects_path()

        if not DataLoader.check_file_exists(projects_path):
            return []

        # List all project directories
        project_dirs = DataLoader.list_directories(projects_path)

        for project_dir in project_dirs:
            try:
                # Try to load project from metadata file
                project = ProjectSummary.from_file(project_dir)
                projects.append(project)
            except (FileNotFoundError, ValueError):
                # Skip directories that don't contain valid projects
                continue

        return projects

    def get_project(self, project_id: str) -> ProjectSummary:
        """
        Get a single project by its ID.

        Args:
            project_id: The ID of the project to retrieve

        Returns:
            The project with the specified ID

        Raises:
            FileNotFoundError: If the project doesn't exist
        """
        projects_path = PathFinder.get_projects_path()
        project_path = projects_path / project_id

        if not DataLoader.check_file_exists(project_path):
            raise FileNotFoundError()

        return ProjectSummary.from_file(project_path)

    def insert_project(self, project: ProjectSummary) -> ProjectSummary:
        """
        Create or update a project.

        Args:
            project: The project to create or update

        Returns:
            The created/updated project
        """
        # Check if project already exists
        try:
            self.get_project(project.id)
            # Update existing project
            self._update_project_metadata(project)
        except FileNotFoundError:
            # Create new project
            self._create_new_project(project)

        return project

    def _update_project_metadata(self, project: ProjectSummary) -> None:
        """
        Update the metadata file for an existing project.

        Args:
            project: The project to update
        """
        project_path = PathFinder.get_project_path(project)
        metadata_path = project_path / FileConstants.METADATA_SUFFIX
        project_data = {"project": project.model_dump()}
        DataWriter.write_yaml(metadata_path, project_data)

    def delete_project(self, project_id: str) -> None:
        """
        Delete a project and all its associated files.

        Args:
            project_id: The ID of the project to delete
        """
        # Get project to ensure it exists
        project = self.get_project(project_id)

        # Delete entire project directory
        DataLoader.delete_entire_project_folder(project)

    def upsert_project(
        self,
        *,
        id: str,  # noqa: A002
        description: Optional[str] = None,
        label: Optional[str] = None,
        location: Optional[str] = None,
        metadata_version: Optional[str] = "1.0",
        status: Optional[str] = None,
        **kwargs,
    ) -> ProjectSummary:
        """
        Create or update a project with the given parameters.

        Args:
            id: Unique project identifier
            description: Optional project description
            label: Optional project label
            location: Optional project location
            metadata_version: Project metadata version (default: "1.0")
            status: Optional project status
            **kwargs: Additional arguments

        Returns:
            The created/updated project
        """
        # Create ProjectSummary from parameters
        project_data: dict[str, str] = {
            "id": id,
            "metadata_version": metadata_version or "1.0",
        }

        # Add optional fields if provided
        if description is not None:
            project_data["description"] = description
        if label is not None:
            project_data["label"] = label
        if location is not None:
            project_data["location"] = location
        if status is not None:
            project_data["status"] = status

        # Add any additional kwargs (filtered to strings only)
        for key, value in kwargs.items():
            if isinstance(value, str):
                project_data[key] = value

        project = ProjectSummary(**project_data)
        return self.insert_project(project)
