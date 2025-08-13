"""Unit tests for Parameter and ParameterOption models."""

import pytest
from pydantic import ValidationError

from fluidize.core.types.parameters import Parameter, ParameterOption


class TestParameterOption:
    """Test suite for ParameterOption model."""

    def test_parameter_option_creation(self):
        """Test ParameterOption creation with required fields."""
        option = ParameterOption(value="option1", label="Option 1")

        assert option.value == "option1"
        assert option.label == "Option 1"

    def test_parameter_option_validation(self):
        """Test ParameterOption field validation."""
        # Test with missing required fields
        with pytest.raises(ValidationError):
            ParameterOption()

        with pytest.raises(ValidationError):
            ParameterOption(value="option1")

        with pytest.raises(ValidationError):
            ParameterOption(label="Option 1")

    def test_parameter_option_serialization(self):
        """Test ParameterOption serialization."""
        option = ParameterOption(value="option1", label="Option 1")
        data = option.model_dump()

        expected = {"value": "option1", "label": "Option 1"}
        assert data == expected


class TestParameter:
    """Test suite for Parameter model."""

    def test_parameter_creation_required_fields(self):
        """Test Parameter creation with only required fields."""
        param = Parameter(
            value="test_value", description="Test description", type="text", label="Test Label", name="test_param"
        )

        assert param.value == "test_value"
        assert param.description == "Test description"
        assert param.type == "text"
        assert param.label == "Test Label"
        assert param.name == "test_param"
        assert param.latex is None
        assert param.location is None
        assert param.options is None
        assert param.scope is None

    def test_parameter_creation_all_fields(self):
        """Test Parameter creation with all fields including optional ones."""
        options = [ParameterOption(value="opt1", label="Option 1"), ParameterOption(value="opt2", label="Option 2")]

        param = Parameter(
            value="test_value",
            description="Test description",
            type="dropdown",
            label="Test Label",
            name="test_param",
            latex="\\alpha",
            location=["section1", "subsection2"],
            options=options,
            scope="global",
        )

        assert param.value == "test_value"
        assert param.description == "Test description"
        assert param.type == "dropdown"
        assert param.label == "Test Label"
        assert param.name == "test_param"
        assert param.latex == "\\alpha"
        assert param.location == ["section1", "subsection2"]
        assert len(param.options) == 2
        assert param.options[0].value == "opt1"
        assert param.options[1].label == "Option 2"
        assert param.scope == "global"

    def test_parameter_validation(self):
        """Test Parameter field validation."""
        # Test with missing required fields
        with pytest.raises(ValidationError):
            Parameter()

        with pytest.raises(ValidationError):
            Parameter(value="test")

        with pytest.raises(ValidationError):
            Parameter(
                value="test",
                description="desc",
                type="text",
                label="label",
                # Missing name
            )

    def test_parameter_optional_fields(self):
        """Test Parameter with various combinations of optional fields."""
        # Test with latex only
        param = Parameter(
            value="test_value",
            description="Test description",
            type="text",
            label="Test Label",
            name="test_param",
            latex="\\beta",
        )

        assert param.latex == "\\beta"
        assert param.location is None
        assert param.options is None
        assert param.scope is None

        # Test with location only
        param = Parameter(
            value="test_value",
            description="Test description",
            type="text",
            label="Test Label",
            name="test_param",
            location=["config", "advanced"],
        )

        assert param.location == ["config", "advanced"]
        assert param.latex is None

    def test_parameter_serialization(self):
        """Test Parameter serialization to dict."""
        options = [ParameterOption(value="opt1", label="Option 1")]

        param = Parameter(
            value="test_value",
            description="Test description",
            type="dropdown",
            label="Test Label",
            name="test_param",
            latex="\\gamma",
            location=["section1"],
            options=options,
            scope="local",
        )

        data = param.model_dump()

        assert data["value"] == "test_value"
        assert data["description"] == "Test description"
        assert data["type"] == "dropdown"
        assert data["label"] == "Test Label"
        assert data["name"] == "test_param"
        assert data["latex"] == "\\gamma"
        assert data["location"] == ["section1"]
        assert len(data["options"]) == 1
        assert data["options"][0]["value"] == "opt1"
        assert data["scope"] == "local"

    def test_parameter_from_dict(self):
        """Test Parameter creation from dictionary."""
        data = {
            "value": "test_value",
            "description": "Test description",
            "type": "text",
            "label": "Test Label",
            "name": "test_param",
            "latex": "\\delta",
            "location": ["section1", "subsection2"],
            "options": [{"value": "opt1", "label": "Option 1"}, {"value": "opt2", "label": "Option 2"}],
            "scope": "global",
        }

        param = Parameter(**data)

        assert param.value == "test_value"
        assert param.latex == "\\delta"
        assert param.location == ["section1", "subsection2"]
        assert len(param.options) == 2
        assert param.options[0].value == "opt1"
        assert param.scope == "global"

    def test_parameter_different_types(self):
        """Test Parameter with different type values."""
        type_values = ["text", "dropdown", "number", "checkbox", "slider"]

        for param_type in type_values:
            param = Parameter(
                value="test_value",
                description="Test description",
                type=param_type,
                label="Test Label",
                name="test_param",
            )

            assert param.type == param_type

    def test_parameter_edge_cases(self):
        """Test Parameter with edge cases."""
        # Test with empty location list
        param = Parameter(
            value="test_value",
            description="Test description",
            type="text",
            label="Test Label",
            name="test_param",
            location=[],
        )

        assert param.location == []

        # Test with empty options list
        param = Parameter(
            value="test_value",
            description="Test description",
            type="dropdown",
            label="Test Label",
            name="test_param",
            options=[],
        )

        assert param.options == []

        # Test with empty strings (valid but unusual)
        param = Parameter(value="", description="", type="", label="", name="", latex="", scope="")

        assert param.value == ""
        assert param.latex == ""
        assert param.scope == ""

    def test_parameter_json_serialization(self):
        """Test Parameter JSON serialization."""
        param = Parameter(
            value="test_value", description="Test description", type="text", label="Test Label", name="test_param"
        )

        json_str = param.model_dump_json()

        # Should be valid JSON containing all fields
        assert '"value":"test_value"' in json_str
        assert '"description":"Test description"' in json_str
        assert '"type":"text"' in json_str
        assert '"label":"Test Label"' in json_str
        assert '"name":"test_param"' in json_str
        # Optional fields should be null
        assert '"latex":null' in json_str
        assert '"location":null' in json_str
        assert '"options":null' in json_str
        assert '"scope":null' in json_str
