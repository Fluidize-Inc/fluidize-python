"""
Custom exceptions for the Fluidize project.

This module provides custom exception classes for better error handling
and debugging throughout the Fluidize application.
"""


class FluidizeError(Exception):
    """Base exception class for all Fluidize-related errors."""

    pass


class ProjectAlreadyExistsError(FluidizeError):
    """Raised when attempting to create a project that already exists."""

    def __init__(self, project_id: str) -> None:
        """
        Initialize the exception.

        Args:
            project_id: The ID of the project that already exists
        """
        super().__init__(f"Project '{project_id}' already exists. Use update to modify existing projects.")
        self.project_id = project_id
