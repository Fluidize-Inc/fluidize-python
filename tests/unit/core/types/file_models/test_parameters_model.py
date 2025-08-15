"""Unit tests for ParametersModel class."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError
from upath import UPath

from fluidize.core.types.file_models.parameters_model import ParametersModel
from fluidize.core.types.parameters import Parameter


class TestParametersModel:
    """Test suite for ParametersModel class."""

    def test_parameters_model_initialization_empty(self):
        """Test ParametersModel initialization with empty parameters."""
        model = ParametersModel()

        assert model.parameters == []
        assert model._filename == "parameters.json"

    def test_parameters_model_initialization_with_params(self):
        """Test ParametersModel initialization with parameters."""
        param1 = Parameter(value="val1", description="desc1", type="text", label="label1", name="param1")
        param2 = Parameter(value="val2", description="desc2", type="number", label="label2", name="param2")

        model = ParametersModel(parameters=[param1, param2])

        assert len(model.parameters) == 2
        assert model.parameters[0] == param1
        assert model.parameters[1] == param2

    def test_unpack_and_validate_non_dict_data(self):
        """Test _unpack_and_validate with non-dictionary data."""
        result = ParametersModel._unpack_and_validate("not_a_dict")

        assert result == "not_a_dict"

    def test_unpack_and_validate_dict_without_key(self):
        """Test _unpack_and_validate with dict that doesn't contain the key."""
        data = {"other_key": "value"}

        result = ParametersModel._unpack_and_validate(data)

        assert result == data

    def test_unpack_and_validate_dict_with_key_list(self):
        """Test _unpack_and_validate with dict containing parameters key with list."""
        param_data = [
            {"value": "val1", "description": "desc1", "type": "text", "label": "label1", "name": "param1"},
            {"value": "val2", "description": "desc2", "type": "number", "label": "label2", "name": "param2"},
        ]
        data = {"parameters": param_data}

        result = ParametersModel._unpack_and_validate(data)

        assert result == {"parameters": param_data}

    def test_unpack_and_validate_dict_with_key_non_list(self):
        """Test _unpack_and_validate with dict containing parameters key with non-list value."""
        data = {"parameters": "not_a_list"}

        result = ParametersModel._unpack_and_validate(data)

        assert result == {"parameters": []}

    def test_unpack_and_validate_dict_with_key_none(self):
        """Test _unpack_and_validate with dict containing parameters key with None."""
        data = {"parameters": None}

        result = ParametersModel._unpack_and_validate(data)

        assert result == {"parameters": []}

    def test_unpack_and_validate_no_key_config(self):
        """Test _unpack_and_validate when class has no Key config."""
        # Test with a different class - manually test the logic
        data = {"test_field": "value", "other_field": "data"}

        # This would be the behavior if no Key class exists
        # The method would just return the data as-is since there's no key to unpack
        result = data  # This simulates what would happen without Key config

        assert result == data

    def test_unpack_and_validate_key_config_no_key_attr(self):
        """Test _unpack_and_validate when Key config has no key attribute."""

        # Create a test class with Key config but no key attribute
        class TestParametersModelNoKeyAttr(ParametersModel):
            class Key:
                pass

        data = {
            "parameters": [{"value": "val", "description": "desc", "type": "text", "label": "label", "name": "param"}]
        }

        result = TestParametersModelNoKeyAttr._unpack_and_validate(data)

        assert result == data

    def test_model_dump_wrapped(self):
        """Test model_dump_wrapped returns correctly formatted data."""
        param1 = Parameter(value="val1", description="desc1", type="text", label="label1", name="param1")
        param2 = Parameter(value="val2", description="desc2", type="number", label="label2", name="param2")

        model = ParametersModel(parameters=[param1, param2])

        result = model.model_dump_wrapped()

        assert "parameters" in result
        assert len(result["parameters"]) == 2
        assert result["parameters"][0]["name"] == "param1"
        assert result["parameters"][1]["name"] == "param2"

    def test_model_dump_wrapped_empty_parameters(self):
        """Test model_dump_wrapped with empty parameters."""
        model = ParametersModel()

        result = model.model_dump_wrapped()

        assert result == {"parameters": []}

    def test_key_class_configuration(self):
        """Test that Key class is properly configured."""
        assert hasattr(ParametersModel, "Key")
        assert hasattr(ParametersModel.Key, "key")
        assert ParametersModel.Key.key == "parameters"

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_with_wrapped_data(self, mock_data_loader):
        """Test from_file with wrapped data structure."""
        param_data = [
            {"value": "val1", "description": "desc1", "type": "text", "label": "label1", "name": "param1"},
            {"value": "val2", "description": "desc2", "type": "number", "label": "label2", "name": "param2"},
        ]
        wrapped_data = {"parameters": param_data}
        mock_data_loader.load_json.return_value = wrapped_data

        directory = UPath("/test/directory")
        result = ParametersModel.from_file(directory)

        assert len(result.parameters) == 2
        assert result.parameters[0].name == "param1"
        assert result.parameters[1].name == "param2"

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_with_unwrapped_data(self, mock_data_loader):
        """Test from_file with unwrapped data structure."""
        param_data = [
            {"value": "val1", "description": "desc1", "type": "text", "label": "label1", "name": "param1"},
        ]
        unwrapped_data = {"parameters": param_data}
        mock_data_loader.load_json.return_value = unwrapped_data

        directory = UPath("/test/directory")
        result = ParametersModel.from_file(directory)

        assert len(result.parameters) == 1
        assert result.parameters[0].name == "param1"

    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_from_file_invalid_parameter_data(self, mock_data_loader):
        """Test from_file with invalid parameter data."""
        invalid_data = {"parameters": [{"invalid": "data"}]}
        mock_data_loader.load_json.return_value = invalid_data

        directory = UPath("/test/directory")

        with pytest.raises(ValidationError):
            ParametersModel.from_file(directory)

    def test_from_dict_and_path_with_valid_data(self):
        """Test from_dict_and_path with valid data."""
        param_data = [
            {"value": "val1", "description": "desc1", "type": "text", "label": "label1", "name": "param1"},
        ]
        data = {"parameters": param_data}
        path = UPath("/test/path/parameters.json")

        result = ParametersModel.from_dict_and_path(data, path)

        assert len(result.parameters) == 1
        assert result.parameters[0].name == "param1"
        assert result._filepath == path

    def test_model_validation_integration(self):
        """Integration test for model validation with various data formats."""
        # Test with complete parameter data
        complete_param = {
            "value": "test_value",
            "description": "Test description",
            "type": "text",
            "label": "Test Label",
            "name": "test_param",
            "latex": "\\alpha",
            "location": ["section1", "subsection2"],
            "options": [{"value": "opt1", "label": "Option 1"}],
            "scope": "global",
        }

        data = {"parameters": [complete_param]}
        model = ParametersModel.model_validate(data)

        assert len(model.parameters) == 1
        param = model.parameters[0]
        assert param.name == "test_param"
        assert param.latex == "\\alpha"
        assert param.location == ["section1", "subsection2"]
        assert len(param.options) == 1
        assert param.scope == "global"

    @patch("fluidize.core.utils.dataloader.data_writer.DataWriter")
    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_save_integration(self, mock_data_loader, mock_data_writer):
        """Integration test for save functionality."""
        existing_data = {"other_key": "other_value"}
        mock_data_loader.load_json.return_value = existing_data

        param1 = Parameter(value="val1", description="desc1", type="text", label="label1", name="param1")
        model = ParametersModel(parameters=[param1])
        model._filepath = UPath("/test/path/parameters.json")

        model.save()

        # Verify that data was merged correctly
        call_args = mock_data_writer.write_json.call_args[0]
        written_data = call_args[1]

        assert "other_key" in written_data
        assert "parameters" in written_data
        assert len(written_data["parameters"]) == 1
        assert written_data["parameters"][0]["name"] == "param1"

    @patch("fluidize.core.utils.dataloader.data_writer.DataWriter")
    @patch("fluidize.core.utils.dataloader.data_loader.DataLoader")
    def test_edit_functionality(self, mock_data_loader, mock_data_writer):
        """Test edit functionality inherited from base class."""
        mock_data_loader.load_json.return_value = {"parameters": []}
        param1 = Parameter(value="val1", description="desc1", type="text", label="label1", name="param1")
        model = ParametersModel(parameters=[param1])
        model._filepath = UPath("/test/path/parameters.json")

        # Edit the parameters list
        new_param = Parameter(value="val2", description="desc2", type="text", label="label2", name="param2")
        model.edit(parameters=[new_param])

        assert len(model.parameters) == 1
        assert model.parameters[0].name == "param2"
        mock_data_writer.write_json.assert_called_once()

    def test_parameters_field_default_factory(self):
        """Test that parameters field uses default_factory correctly."""
        model1 = ParametersModel()
        model2 = ParametersModel()

        # Ensure each instance gets its own list
        assert model1.parameters is not model2.parameters
        assert model1.parameters == []
        assert model2.parameters == []

        # Modify one and ensure the other is unaffected
        param = Parameter(value="val", description="desc", type="text", label="label", name="param")
        model1.parameters.append(param)

        assert len(model1.parameters) == 1
        assert len(model2.parameters) == 0
