"""Unit tests for JSONFileModelBase class."""

import json
import tempfile
from typing import ClassVar
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from upath import UPath

from fluidize.core.types.file_models.json_file_model_base import JSONFileModelBase


class MockJSONFileModel(JSONFileModelBase):
    """Test implementation of JSONFileModelBase."""

    _filename: ClassVar[str] = "test.json"
    test_field: str = "default_value"

    # Configure to forbid extra fields for validation tests
    model_config: ClassVar = {"extra": "forbid"}

    class Key:
        key = "test_key"


class MockJSONFileModelNoKey(JSONFileModelBase):
    """Test implementation without Key configuration."""

    _filename: ClassVar[str] = "test_no_key.json"
    test_field: str = "default_value"


class MockJSONFileModelNoFilename(JSONFileModelBase):
    """Test implementation without _filename."""

    test_field: str = "default_value"


class TestJSONFileModelBase:
    """Test suite for JSONFileModelBase class."""

    def test_filepath_property_with_path(self):
        """Test filepath property when path is set."""
        model = MockJSONFileModel(test_field="test")
        test_path = UPath("/test/path/test.json")
        model._filepath = test_path

        assert model.filepath == test_path

    def test_filepath_property_without_path(self):
        """Test filepath property when path is not set."""
        model = MockJSONFileModel(test_field="test")

        with pytest.raises(ValueError):
            _ = model.filepath

    def test_directory_property(self):
        """Test directory property returns parent of filepath."""
        model = MockJSONFileModel(test_field="test")
        test_path = UPath("/test/path/test.json")
        model._filepath = test_path

        assert model.directory == test_path.parent

    def test_directory_property_without_path(self):
        """Test directory property when filepath is not set."""
        model = MockJSONFileModel(test_field="test")

        with pytest.raises(ValueError):
            _ = model.directory

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_success(self, mock_data_loader):
        """Test successful file loading."""
        mock_data_loader.load_json.return_value = {"test_field": "loaded_value"}
        directory = UPath("/test/directory")

        result = MockJSONFileModel.from_file(directory)

        assert result.test_field == "loaded_value"
        assert result._filepath == directory / "test.json"
        mock_data_loader.load_json.assert_called_once_with(directory / "test.json")

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_no_filename(self, mock_data_loader):
        """Test from_file with class that has no _filename."""
        directory = UPath("/test/directory")

        with pytest.raises(TypeError):
            MockJSONFileModelNoFilename.from_file(directory)

        mock_data_loader.load_json.assert_not_called()

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_empty_data(self, mock_data_loader):
        """Test from_file with empty data."""
        mock_data_loader.load_json.return_value = None
        directory = UPath("/test/directory")

        with pytest.raises(FileNotFoundError):
            MockJSONFileModel.from_file(directory)

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_validation_error(self, mock_data_loader):
        """Test from_file with validation error."""
        mock_data_loader.load_json.return_value = {"invalid_field": "value"}
        directory = UPath("/test/directory")

        with pytest.raises(ValidationError):
            MockJSONFileModel.from_file(directory)

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_other_exception(self, mock_data_loader):
        """Test from_file with other exception during model validation."""
        mock_data_loader.load_json.return_value = {"test_field": "value"}
        directory = UPath("/test/directory")

        with (
            patch.object(MockJSONFileModel, "model_validate", side_effect=RuntimeError("Test error")),
            pytest.raises(ValueError),
        ):
            MockJSONFileModel.from_file(directory)

    def test_from_dict_and_path_success(self):
        """Test successful creation from dict and path."""
        data = {"test_field": "dict_value"}
        path = UPath("/test/path/test.json")

        result = MockJSONFileModel.from_dict_and_path(data, path)

        assert result.test_field == "dict_value"
        assert result._filepath == path

    def test_from_dict_and_path_empty_data(self):
        """Test from_dict_and_path with empty data."""
        data = {}
        path = UPath("/test/path/test.json")

        with pytest.raises(ValueError):
            MockJSONFileModel.from_dict_and_path(data, path)

    def test_from_dict_and_path_validation_error(self):
        """Test from_dict_and_path with validation error."""
        data = {"invalid_field": "value"}
        path = UPath("/test/path/test.json")

        with pytest.raises(ValidationError):
            MockJSONFileModel.from_dict_and_path(data, path)

    def test_from_dict_and_path_other_exception(self):
        """Test from_dict_and_path with other exception during validation."""
        data = {"test_field": "value"}
        path = UPath("/test/path/test.json")

        with (
            patch.object(MockJSONFileModel, "model_validate", side_effect=RuntimeError("Test error")),
            pytest.raises(ValueError),
        ):
            MockJSONFileModel.from_dict_and_path(data, path)

    def test_model_dump_wrapped_with_key(self):
        """Test model_dump_wrapped with Key configuration."""
        model = MockJSONFileModel(test_field="test_value")

        result = model.model_dump_wrapped()

        expected = {"test_key": {"test_field": "test_value"}}
        assert result == expected

    def test_model_dump_wrapped_without_key(self):
        """Test model_dump_wrapped without Key configuration."""
        model = MockJSONFileModelNoKey(test_field="test_value")

        result = model.model_dump_wrapped()

        expected = {"test_field": "test_value"}
        assert result == expected

    def test_model_dump_wrapped_no_key_attribute(self):
        """Test model_dump_wrapped when Key class has no key attribute."""

        # Create a model class with a Key that has no key attribute
        class MockModelNoKeyAttr(JSONFileModelBase):
            _filename: ClassVar[str] = "test.json"
            test_field: str = "default_value"

            class Key:
                pass  # No key attribute

        model = MockModelNoKeyAttr(test_field="test_value")
        result = model.model_dump_wrapped()

        expected = {"test_field": "test_value"}
        assert result == expected

    @patch("fluidize.core.utils.dataloader.data_writer.DataWriter")
    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_save_with_directory(self, mock_data_loader, mock_data_writer):
        """Test save with directory parameter."""
        mock_data_loader.load_json.return_value = {"existing": "data"}
        model = MockJSONFileModel(test_field="test_value")
        directory = UPath("/test/directory")

        model.save(directory)

        expected_path = directory / "test.json"
        assert model._filepath == expected_path
        mock_data_loader.load_json.assert_called_once()
        mock_data_writer.write_json.assert_called_once()

    @patch("fluidize.core.utils.dataloader.data_writer.DataWriter")
    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_save_without_directory(self, mock_data_loader, mock_data_writer):
        """Test save without directory parameter using existing filepath."""
        mock_data_loader.load_json.return_value = {"existing": "data"}
        model = MockJSONFileModel(test_field="test_value")
        model._filepath = UPath("/existing/path/test.json")

        model.save()

        mock_data_loader.load_json.assert_called_once_with(UPath("/existing/path/test.json"))
        mock_data_writer.write_json.assert_called_once()

    def test_save_no_filename_attribute(self):
        """Test save with class that has no _filename attribute."""
        model = MockJSONFileModelNoFilename(test_field="test_value")
        directory = UPath("/test/directory")

        with pytest.raises(TypeError):
            model.save(directory)

    def test_save_no_filepath(self):
        """Test save without filepath and without directory parameter."""
        model = MockJSONFileModel(test_field="test_value")

        with pytest.raises(ValueError):
            model.save()

    @patch("fluidize.core.utils.dataloader.data_writer.DataWriter")
    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_save_data_merge(self, mock_data_loader, mock_data_writer):
        """Test that save merges new data with existing data."""
        existing_data = {"existing_key": "existing_value", "test_key": {"old_field": "old_value"}}
        mock_data_loader.load_json.return_value = existing_data

        model = MockJSONFileModel(test_field="new_value")
        model._filepath = UPath("/test/path/test.json")

        model.save()

        # Check that the data was merged correctly
        call_args = mock_data_writer.write_json.call_args[0]
        written_data = call_args[1]

        assert "existing_key" in written_data
        assert written_data["existing_key"] == "existing_value"
        assert written_data["test_key"]["test_field"] == "new_value"

    @patch("fluidize.core.utils.dataloader.data_writer.DataWriter")
    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_edit_valid_attributes(self, mock_data_loader, mock_data_writer):
        """Test edit with valid attributes."""
        mock_data_loader.load_json.return_value = {"test_key": {"test_field": "original_value"}}
        model = MockJSONFileModel(test_field="original_value")
        model._filepath = UPath("/test/path/test.json")

        model.edit(test_field="new_value")

        assert model.test_field == "new_value"
        mock_data_writer.write_json.assert_called_once()

    def test_edit_invalid_attribute(self):
        """Test edit with invalid attribute."""
        model = MockJSONFileModel(test_field="original_value")
        model._filepath = UPath("/test/path/test.json")

        with pytest.raises(AttributeError):
            model.edit(nonexistent_field="value")

    def test_integration_file_operations(self):
        """Integration test for file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = UPath(temp_dir)
            test_file = directory / "test.json"

            # Create initial file content (only fields the model expects)
            initial_data = {"test_field": "initial_value"}
            with open(test_file, "w") as f:
                json.dump(initial_data, f)

            # Load from file
            model = MockJSONFileModel.from_file(directory)
            assert model.test_field == "initial_value"
            assert model.filepath == test_file

            # Test that methods exist
            assert hasattr(model, "edit")
            assert hasattr(model, "save")
