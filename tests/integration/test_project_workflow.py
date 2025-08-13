"""Integration tests for end-to-end project workflows.

These tests verify that all components work together correctly
without mocking internal dependencies.
"""

import pytest

from fluidize.core.constants import FileConstants


class TestProjectWorkflowIntegration:
    """Integration tests for complete project workflows."""

    def test_complete_project_lifecycle(self, client, integration_temp_dir):
        """Test complete project lifecycle: create → retrieve → update → delete."""
        # Create a project
        project_data = {
            "project_id": "lifecycle-test",
            "label": "Lifecycle Test Project",
            "description": "Testing complete project lifecycle",
            "location": "/test/lifecycle",
            "status": "testing",
        }

        created_project = client.projects.create(**project_data)

        # Verify project was created
        assert created_project.id == project_data["project_id"]
        assert created_project.label == project_data["label"]
        assert created_project.description == project_data["description"]
        assert created_project.location == project_data["location"]
        assert created_project.status == project_data["status"]

        # Verify filesystem structure exists
        project_dir = integration_temp_dir / "projects" / project_data["project_id"]
        assert project_dir.exists()
        assert (project_dir / FileConstants.METADATA_SUFFIX).exists()
        assert (project_dir / FileConstants.GRAPH_SUFFIX).exists()
        assert (project_dir / FileConstants.PARAMETERS_SUFFIX).exists()

        # Retrieve the project
        retrieved_project = client.projects.get(project_data["project_id"])
        assert retrieved_project.id == created_project.id
        assert retrieved_project.label == created_project.label

        # Update the project
        updated_project = client.projects.update(
            project_id=project_data["project_id"], label="Updated Lifecycle Project", status="updated"
        )
        assert updated_project.label == "Updated Lifecycle Project"
        assert updated_project.status == "updated"
        assert updated_project.description == project_data["description"]  # Unchanged

        # Verify update persisted by retrieving again
        re_retrieved_project = client.projects.get(project_data["project_id"])
        assert re_retrieved_project.label == "Updated Lifecycle Project"
        assert re_retrieved_project.status == "updated"

        # List projects should include our project
        all_projects = client.projects.list()
        project_ids = [p.id for p in all_projects]
        assert project_data["project_id"] in project_ids

        # Delete the project (via adapter since client doesn't have delete)
        client.adapter.projects.delete(project_data["project_id"])

        # Verify project is deleted from filesystem
        assert not project_dir.exists()

        # Verify project no longer retrievable
        with pytest.raises(FileNotFoundError):
            client.projects.get(project_data["project_id"])

    def test_multiple_projects_workflow(self, projects_manager, sample_projects_data, integration_temp_dir):
        """Test managing multiple projects simultaneously."""
        created_projects = []

        # Create multiple projects
        for project_data in sample_projects_data:
            # Convert 'id' to 'project_id' for the manager interface
            create_data = {**project_data}
            create_data["project_id"] = create_data.pop("id")
            created_project = projects_manager.create(**create_data)
            created_projects.append(created_project)

            # Verify each project exists in filesystem
            project_dir = integration_temp_dir / "projects" / project_data["id"]
            assert project_dir.exists()

        # List all projects
        all_projects = projects_manager.list()
        assert len(all_projects) == len(sample_projects_data)

        created_ids = {p.id for p in created_projects}
        retrieved_ids = {p.id for p in all_projects}
        assert created_ids == retrieved_ids

        # Update each project
        for i, project in enumerate(created_projects):
            updated_project = projects_manager.update(
                project_id=project.id, label=f"Updated Project {i + 1}", status="batch-updated"
            )
            assert updated_project.label == f"Updated Project {i + 1}"
            assert updated_project.status == "batch-updated"

        # Verify all projects were updated
        updated_projects = projects_manager.list()
        for project in updated_projects:
            assert project.status == "batch-updated"
            assert "Updated Project" in project.label

    def test_project_filesystem_consistency(self, local_adapter, integration_temp_dir):
        """Test that filesystem operations maintain consistency."""
        project_data = {
            "id": "filesystem-test",
            "label": "Filesystem Test",
            "description": "Testing filesystem consistency",
            "location": "/fs/test",
            "status": "testing",
        }

        # Create project
        local_adapter.projects.upsert(**project_data)
        project_dir = integration_temp_dir / "projects" / project_data["id"]

        # Verify all required files exist
        assert project_dir.exists()
        metadata_file = project_dir / FileConstants.METADATA_SUFFIX
        graph_file = project_dir / FileConstants.GRAPH_SUFFIX
        params_file = project_dir / FileConstants.PARAMETERS_SUFFIX

        assert metadata_file.exists()
        assert graph_file.exists()
        assert params_file.exists()

        # Verify file contents are valid
        import json

        import yaml

        with open(metadata_file) as f:
            metadata_content = yaml.safe_load(f)
            assert "project" in metadata_content
            assert metadata_content["project"]["id"] == project_data["id"]

        with open(graph_file) as f:
            graph_content = json.load(f)
            assert "nodes" in graph_content
            assert "edges" in graph_content
            assert graph_content["nodes"] == []
            assert graph_content["edges"] == []

        with open(params_file) as f:
            params_content = json.load(f)
            assert "metadata" in params_content
            assert "parameters" in params_content

        # Update project and verify metadata file changes
        local_adapter.projects.upsert(id=project_data["id"], label="Updated Filesystem Test", status="updated")

        with open(metadata_file) as f:
            updated_metadata = yaml.safe_load(f)
            assert updated_metadata["project"]["label"] == "Updated Filesystem Test"
            assert updated_metadata["project"]["status"] == "updated"

    def test_error_handling_integration(self, projects_manager):
        """Test error handling across the integration stack."""
        # Test retrieving non-existent project
        with pytest.raises(FileNotFoundError):
            projects_manager.get("non-existent-project")

        # Test creating project with invalid data should still work
        # (the system is permissive with string fields)
        try:
            projects_manager.create(
                project_id="error-test",
                label="",  # Empty label should be fine
                description="",  # Empty description should be fine
                location="",  # Empty location should be fine
                status="",  # Empty status should be fine
            )
            # If we get here, the system handled empty strings gracefully
            assert True
        except Exception as e:
            pytest.fail(f"System should handle empty strings gracefully: {e}")

    def test_concurrent_operations_simulation(self, local_adapter, integration_temp_dir):
        """Test operations that might happen concurrently."""
        base_project_data = {
            "id": "concurrent-test",
            "label": "Concurrent Test",
            "description": "Testing concurrent-like operations",
            "status": "active",
        }

        # Create initial project
        local_adapter.projects.upsert(**base_project_data)

        # Simulate concurrent updates (sequential but rapid)
        local_adapter.projects.upsert(id="concurrent-test", label="Updated by Process 1", description="First update")

        local_adapter.projects.upsert(
            id="concurrent-test", label="Updated by Process 2", description="Second update", status="processing"
        )

        # Verify final state
        final_project = local_adapter.projects.retrieve("concurrent-test")
        assert final_project.label == "Updated by Process 2"
        assert final_project.description == "Second update"
        assert final_project.status == "processing"

        # Verify filesystem consistency
        project_dir = integration_temp_dir / "projects" / "concurrent-test"
        metadata_file = project_dir / FileConstants.METADATA_SUFFIX

        import yaml

        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
            assert metadata["project"]["label"] == "Updated by Process 2"

    def test_project_data_persistence(self, client, integration_temp_dir):
        """Test that project data persists correctly between operations."""
        # Create project with special characters and unicode
        project_data = {
            "project_id": "persistence-test-🚀",
            "label": "Persistence Test with émojis and ünïcödë",
            "description": "Testing data persistence with special chars: !@#$%^&*()",
            "location": "/path/with spaces/and-special-chars",
            "status": "unicode-test",
        }

        created_project = client.projects.create(**project_data)

        # Create a new client instance to simulate restart
        from fluidize.client import FluidizeClient

        new_client = FluidizeClient(mode="local")

        # Retrieve project with new client instance
        retrieved_project = new_client.projects.get(project_data["project_id"])

        # Verify all data persisted correctly
        assert retrieved_project.id == created_project.id
        assert retrieved_project.label == created_project.label
        assert retrieved_project.description == created_project.description
        assert retrieved_project.location == created_project.location
        assert retrieved_project.status == created_project.status

        # Verify filesystem encoding handled correctly
        project_dir = integration_temp_dir / "projects" / project_data["project_id"]
        assert project_dir.exists()

    def test_adapter_integration_compatibility(self, local_adapter):
        """Test that adapter provides expected interface for integration."""
        # Test that adapter has expected structure
        assert hasattr(local_adapter, "projects")
        assert hasattr(local_adapter.projects, "list")
        assert hasattr(local_adapter.projects, "retrieve")
        assert hasattr(local_adapter.projects, "upsert")
        assert hasattr(local_adapter.projects, "delete")

        # Test basic operations work
        project_data = {
            "id": "adapter-integration-test",
            "label": "adapter Integration Test",
            "description": "Testing adapter integration",
        }

        # Create
        created = local_adapter.projects.upsert(**project_data)
        assert created.id == project_data["id"]

        # List
        projects = local_adapter.projects.list()

        assert any(p.id == project_data["id"] for p in projects)

        # Retrieve
        retrieved = local_adapter.projects.retrieve(project_data["id"])
        assert retrieved.id == created.id

        # Delete
        result = local_adapter.projects.delete(project_data["id"])
        assert result["success"] is True

        # Verify deletion
        with pytest.raises(FileNotFoundError):
            local_adapter.projects.retrieve(project_data["id"])
