"""Unit tests for graph parameters module."""

import pytest
from pydantic import ValidationError

from fluidize.core.modules.graph.parameters import parse_parameters_from_json
from fluidize.core.types.parameters import Parameter


class TestGraphParameters:
    """Test suite for graph parameters parsing."""

    def test_parse_parameters_from_json_valid_data(self):
        """Test parsing parameters from valid JSON data."""
        data = {
            "parameters": [
                {
                    "value": "test_value_1",
                    "description": "First test parameter",
                    "type": "text",
                    "label": "Test Label 1",
                    "name": "test_param_1",
                },
                {
                    "value": "test_value_2",
                    "description": "Second test parameter",
                    "type": "dropdown",
                    "label": "Test Label 2",
                    "name": "test_param_2",
                    "options": [{"value": "opt1", "label": "Option 1"}, {"value": "opt2", "label": "Option 2"}],
                },
            ]
        }

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 2

        # Check first parameter
        assert isinstance(parameters[0], Parameter)
        assert parameters[0].value == "test_value_1"
        assert parameters[0].name == "test_param_1"
        assert parameters[0].type == "text"

        # Check second parameter
        assert isinstance(parameters[1], Parameter)
        assert parameters[1].value == "test_value_2"
        assert parameters[1].name == "test_param_2"
        assert parameters[1].type == "dropdown"
        assert len(parameters[1].options) == 2

    def test_parse_parameters_from_json_empty_list(self):
        """Test parsing parameters from JSON with empty parameters list."""
        data = {"parameters": []}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_parse_parameters_from_json_missing_parameters(self):
        """Test parsing parameters from JSON without parameters key."""
        data = {"other_data": "some_value"}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_parse_parameters_from_json_null_parameters(self):
        """Test parsing parameters from JSON with null parameters."""
        data = {"parameters": None}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_parse_parameters_from_json_invalid_parameters_type(self):
        """Test parsing parameters from JSON with non-list parameters."""
        data = {"parameters": "not_a_list"}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_parse_parameters_from_json_invalid_parameter_data(self):
        """Test parsing parameters from JSON with invalid parameter data."""
        data = {
            "parameters": [
                {
                    "value": "test_value",
                    "description": "Test parameter",
                    "type": "text",
                    "label": "Test Label",
                    # Missing required 'name' field
                }
            ]
        }

        with pytest.raises(ValidationError):
            parse_parameters_from_json(data)

    def test_parse_parameters_from_json_mixed_valid_invalid(self):
        """Test parsing parameters with one valid and one invalid parameter."""
        data = {
            "parameters": [
                {
                    "value": "test_value_1",
                    "description": "Valid parameter",
                    "type": "text",
                    "label": "Test Label 1",
                    "name": "test_param_1",
                },
                {
                    "value": "test_value_2",
                    "description": "Invalid parameter",
                    "type": "text",
                    "label": "Test Label 2",
                    # Missing required 'name' field
                },
            ]
        }

        # Should raise ValidationError on the invalid parameter
        with pytest.raises(ValidationError):
            parse_parameters_from_json(data)

    def test_parse_parameters_from_json_with_all_optional_fields(self):
        """Test parsing parameters with all optional fields filled."""
        data = {
            "parameters": [
                {
                    "value": "test_value",
                    "description": "Test parameter with all fields",
                    "type": "dropdown",
                    "label": "Test Label",
                    "name": "test_param",
                    "latex": "\\alpha",
                    "location": ["section1", "subsection2"],
                    "options": [{"value": "opt1", "label": "Option 1"}, {"value": "opt2", "label": "Option 2"}],
                    "scope": "global",
                }
            ]
        }

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 1
        param = parameters[0]

        assert param.value == "test_value"
        assert param.description == "Test parameter with all fields"
        assert param.type == "dropdown"
        assert param.label == "Test Label"
        assert param.name == "test_param"
        assert param.latex == "\\alpha"
        assert param.location == ["section1", "subsection2"]
        assert len(param.options) == 2
        assert param.scope == "global"

    def test_parse_parameters_from_json_empty_dict(self):
        """Test parsing parameters from empty dictionary."""
        data = {}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_parse_parameters_from_json_parameters_is_dict(self):
        """Test parsing parameters when 'parameters' is a dict instead of list."""
        data = {"parameters": {"param1": "value1", "param2": "value2"}}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_parse_parameters_from_json_parameters_is_number(self):
        """Test parsing parameters when 'parameters' is a number."""
        data = {"parameters": 42}

        parameters = parse_parameters_from_json(data)

        assert len(parameters) == 0
        assert isinstance(parameters, list)

    def test_function_import(self):
        """Test that the function can be imported correctly."""
        from fluidize.core.modules.graph.parameters import parse_parameters_from_json

        assert callable(parse_parameters_from_json)
        assert parse_parameters_from_json.__name__ == "parse_parameters_from_json"

    def test_parameter_type_import(self):
        """Test that Parameter type is properly imported."""
        from fluidize.core.modules.graph.parameters import Parameter

        # Should be able to create a Parameter instance
        param = Parameter(value="test", description="test desc", type="text", label="test label", name="test_name")

        assert isinstance(param, Parameter)
        assert param.name == "test_name"
