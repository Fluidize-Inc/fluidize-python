from typing import Any, Optional

from .project import Project


class Projects:
    """Manager for project-related operations."""

    def __init__(self, backend: Any) -> None:
        """
        Initialize the Projects manager.

        Args:
            backend: Backend adapter (FluidizeSDK or LocalBackend)
        """
        self.backend = backend

    def create(
        self,
        project_id: str,
        label: str = "",
        description: str = "",
        location: str = "",
        status: str = "",
    ) -> Project:
        """
        Create a new project.

        Args:
            project_id: Unique identifier for the project
            label: Display label for the project
            description: Project description
            location: Project location
            status: Project status

        Returns:
            Created project wrapped in Project class
        """
        project_summary = self.backend.projects.upsert(
            id=project_id,
            label=label,
            description=description,
            location=location,
            status=status,
        )
        return Project(self.backend, project_summary)

    def get(self, project_id: str) -> Project:
        """
        Get a project by ID.

        Args:
            project_id: The project ID

        Returns:
            Project wrapped in Project class
        """
        project_summary = self.backend.projects.retrieve(project_id)
        return Project(self.backend, project_summary)

    def list(self) -> list[Project]:
        """
        List all projects.

        Returns:
            List of projects wrapped in Project class
        """
        project_summaries = self.backend.projects.list()
        return [Project(self.backend, summary) for summary in project_summaries]

    def update(
        self,
        project_id: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Project:
        """
        Update an existing project.

        Args:
            project_id: The project ID to update
            label: New label
            description: New description
            location: New location
            status: New status

        Returns:
            Updated project wrapped in Project class
        """
        # Build update data, only include non-None values
        update_data = {"id": project_id}
        if label is not None:
            update_data["label"] = label
        if description is not None:
            update_data["description"] = description
        if location is not None:
            update_data["location"] = location
        if status is not None:
            update_data["status"] = status

        project_summary = self.backend.projects.upsert(**update_data)
        return Project(self.backend, project_summary)
