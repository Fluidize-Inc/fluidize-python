"""
Local projects handler - uses core ProjectProcessor for filesystem operations.
"""

from typing import Any, Optional

from fluidize.core.modules.projects.processor import ProjectProcessor
from fluidize.core.types.project import ProjectSummary


class ProjectsHandler:
    """Handles project operations for local mode - matches SDK interface."""

    def __init__(self, config: Any) -> None:
        """
        Initialize the projects handler.

        Args:
            config: FluidizeConfig instance
        """
        self.config = config
        self.processor = ProjectProcessor()

    def delete(self, project_id: str) -> dict:
        """
        Delete a project based on its ID.

        Args:
            project_id: The project ID to delete

        Returns:
            Dict indicating success
        """
        self.processor.delete_project(project_id)
        return {"success": True, "message": f"Project {project_id} deleted"}

    def list(self) -> list[ProjectSummary]:
        """
        Get a summary of all projects.

        Returns:
            List of project summaries
        """
        return self.processor.get_projects()

    def retrieve(self, project_id: str) -> ProjectSummary:
        """
        Get a project by its ID.

        Args:
            project_id: The project ID to retrieve

        Returns:
            ProjectSummary (project data)
        """
        return self.processor.get_project(project_id)

    def upsert(
        self,
        *,
        id: str,  # noqa: A002
        description: Optional[str] = None,
        label: Optional[str] = None,
        location: Optional[str] = None,
        metadata_version: Optional[str] = "1.0",
        status: Optional[str] = None,
        **kwargs: Any,
    ) -> ProjectSummary:
        """
        Create or update a project.

        Args:
            id: Unique project identifier  # noqa: A002
            description: Optional project description
            label: Optional project label
            location: Optional project location
            metadata_version: Project metadata version (default: "1.0")
            status: Optional project status
            **kwargs: Additional arguments

        Returns:
            ProjectSummary (created/updated project data)
        """
        return self.processor.upsert_project(
            id=id,
            description=description,
            label=label,
            location=location,
            metadata_version=metadata_version,
            status=status,
            **kwargs,
        )
