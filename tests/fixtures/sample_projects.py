"""Sample project data for testing."""

from fluidize.core.types.project import ProjectSummary


class SampleProjects:
    """Collection of sample project data for testing."""

    @staticmethod
    def standard_project() -> ProjectSummary:
        """Standard project with all fields populated."""
        return ProjectSummary(
            id="sample-project-001",
            label="Sample Project",
            description="A comprehensive sample project for testing purposes",
            status="active",
            location="/sample/project/location",
            metadata_version="1.0",
        )

    @staticmethod
    def minimal_project() -> ProjectSummary:
        """Minimal project with only required fields."""
        return ProjectSummary(id="minimal-001", metadata_version="1.0")

    @staticmethod
    def project_with_special_chars() -> ProjectSummary:
        """Project with special characters for edge case testing."""
        return ProjectSummary(
            id="special-chars-project",
            label="Test Project with Special Chars: !@#$%^&*()",
            description="Description with\nnewlines and\ttabs and 'quotes'",
            status="test-status",
            location="/path/with spaces/and-special-chars",
            metadata_version="1.0",
        )

    @staticmethod
    def projects_for_listing() -> list[ProjectSummary]:
        """Multiple projects for testing list operations."""
        return [
            ProjectSummary(
                id="list-project-001",
                label="First Project",
                description="First project in the list",
                status="active",
                location="/list/test/1",
                metadata_version="1.0",
            ),
            ProjectSummary(
                id="list-project-002",
                label="Second Project",
                description="Second project in the list",
                status="pending",
                location="/list/test/2",
                metadata_version="1.0",
            ),
            ProjectSummary(
                id="list-project-003",
                label="Third Project",
                description="Third project in the list",
                status="completed",
                location="/list/test/3",
                metadata_version="1.0",
            ),
        ]

    @staticmethod
    def project_update_data() -> dict:
        """Sample data for project updates."""
        return {
            "label": "Updated Project Label",
            "description": "This project has been updated",
            "status": "updated",
            "location": "/updated/location",
        }

    @staticmethod
    def project_creation_params() -> dict:
        """Parameters for project creation testing."""
        return {
            "project_id": "creation-test-001",
            "label": "Created Project",
            "description": "Project created via parameters",
            "location": "/created/project/path",
            "status": "created",
        }

    @staticmethod
    def invalid_project_data() -> list[dict]:
        """Invalid project data for error testing."""
        return [
            # Missing required ID
            {"label": "No ID Project", "description": "This project has no ID", "metadata_version": "1.0"},
            # Invalid metadata version
            {"id": "invalid-version", "metadata_version": "999.0"},
            # Empty ID
            {"id": "", "metadata_version": "1.0"},
        ]
