"""
Project wrapper that provides convenient access to project data and operations.
"""

from typing import Any, Optional

from fluidize.core.types.project import ProjectSummary

from .project_graph import ProjectGraph


class Project:
    """
    Project wrapper that provides convenient access to project operations.

    This class wraps a ProjectSummary and adds convenient properties like
    graph access while maintaining compatibility with all existing project data.
    """

    def __init__(self, backend: Any, project_summary: ProjectSummary) -> None:
        """
        Initialize project wrapper.

        Args:
            backend: Backend adapter (FluidizeSDK or LocalBackend)
            project_summary: The underlying project data
        """
        self._backend = backend
        self._project_summary = project_summary
        self._graph: Optional[ProjectGraph] = None

    @property
    def graph(self) -> ProjectGraph:
        """
        Get the graph manager for this project.

        Returns:
            ProjectGraph manager scoped to this project
        """
        if self._graph is None:
            self._graph = ProjectGraph(self._backend, self._project_summary)
        return self._graph

    # Delegate all ProjectSummary attributes
    @property
    def id(self) -> str:
        """Get project ID."""
        return self._project_summary.id

    @property
    def label(self) -> Optional[str]:
        """Get project label."""
        return self._project_summary.label

    @property
    def description(self) -> Optional[str]:
        """Get project description."""
        return self._project_summary.description

    @property
    def location(self) -> Optional[str]:
        """Get project location."""
        return self._project_summary.location

    @property
    def status(self) -> Optional[str]:
        """Get project status."""
        return self._project_summary.status

    @property
    def metadata_version(self) -> str:
        """Get project metadata version."""
        return self._project_summary.metadata_version

    @property
    def created_at(self) -> Optional[str]:
        """Get project creation timestamp."""
        return getattr(self._project_summary, "created_at", None)

    @property
    def updated_at(self) -> Optional[str]:
        """Get project update timestamp."""
        return getattr(self._project_summary, "updated_at", None)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert project to dictionary representation.

        Returns:
            Dictionary representation of the project
        """
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "location": self.location,
            "status": self.status,
            "metadata_version": self.metadata_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"Project(id='{self.id}', label='{self.label}')"

    def __str__(self) -> str:
        return f"Project {self.id}: {self.label or 'No label'}"
