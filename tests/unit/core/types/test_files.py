"""Unit tests for FileMetadata model."""

import pytest
from pydantic import ValidationError

from fluidize.core.types.files import FileMetadata


class TestFileMetadata:
    """Test suite for FileMetadata model."""

    def test_file_metadata_creation(self):
        """Test FileMetadata creation with all fields."""
        metadata = FileMetadata(
            path="/path/to/file", filename="test.py", size=1024, mime_type="text/x-python", language="python"
        )

        assert metadata.path == "/path/to/file"
        assert metadata.filename == "test.py"
        assert metadata.size == 1024
        assert metadata.mime_type == "text/x-python"
        assert metadata.language == "python"

    def test_file_metadata_validation(self):
        """Test FileMetadata field validation."""
        # Test with missing required fields
        with pytest.raises(ValidationError):
            FileMetadata()

        with pytest.raises(ValidationError):
            FileMetadata(path="/path/to/file")

        with pytest.raises(ValidationError):
            FileMetadata(
                path="/path/to/file",
                filename="test.py",
                # Missing size, mime_type, language
            )

    def test_file_metadata_serialization(self):
        """Test FileMetadata serialization to dict."""
        metadata = FileMetadata(
            path="/path/to/file", filename="test.py", size=1024, mime_type="text/x-python", language="python"
        )

        data = metadata.model_dump()
        expected = {
            "path": "/path/to/file",
            "filename": "test.py",
            "size": 1024,
            "mime_type": "text/x-python",
            "language": "python",
        }

        assert data == expected

    def test_file_metadata_from_dict(self):
        """Test FileMetadata creation from dictionary."""
        data = {
            "path": "/path/to/file",
            "filename": "test.py",
            "size": 1024,
            "mime_type": "text/x-python",
            "language": "python",
        }

        metadata = FileMetadata(**data)

        assert metadata.path == "/path/to/file"
        assert metadata.filename == "test.py"
        assert metadata.size == 1024
        assert metadata.mime_type == "text/x-python"
        assert metadata.language == "python"

    def test_file_metadata_json_serialization(self):
        """Test FileMetadata JSON serialization."""
        metadata = FileMetadata(
            path="/path/to/file", filename="test.py", size=1024, mime_type="text/x-python", language="python"
        )

        json_str = metadata.model_dump_json()

        # Should be valid JSON containing all fields
        assert '"path":"/path/to/file"' in json_str
        assert '"filename":"test.py"' in json_str
        assert '"size":1024' in json_str
        assert '"mime_type":"text/x-python"' in json_str
        assert '"language":"python"' in json_str

    def test_file_metadata_edge_cases(self):
        """Test FileMetadata with edge cases."""
        # Test with empty strings (valid but unusual)
        metadata = FileMetadata(path="", filename="", size=0, mime_type="", language="")

        assert metadata.path == ""
        assert metadata.filename == ""
        assert metadata.size == 0
        assert metadata.mime_type == ""
        assert metadata.language == ""

        # Test with very long strings
        long_path = "/very/long/path/" + "a" * 1000
        metadata = FileMetadata(
            path=long_path, filename="test.py", size=999999999, mime_type="text/x-python", language="python"
        )

        assert metadata.path == long_path
        assert metadata.size == 999999999

    def test_file_metadata_type_validation(self):
        """Test FileMetadata type validation."""
        # Test invalid size type
        with pytest.raises(ValidationError):
            FileMetadata(
                path="/path/to/file",
                filename="test.py",
                size="invalid",  # Should be int
                mime_type="text/x-python",
                language="python",
            )

        # Test negative size (should be valid as Pydantic doesn't restrict it)
        metadata = FileMetadata(
            path="/path/to/file", filename="test.py", size=-1, mime_type="text/x-python", language="python"
        )

        assert metadata.size == -1
