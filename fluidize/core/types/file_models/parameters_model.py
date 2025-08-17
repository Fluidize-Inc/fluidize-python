from typing import Any, ClassVar

from pydantic import Field, model_validator

from fluidize.core.constants import FileConstants
from fluidize.core.types.parameters import Parameter

from .json_file_model_base import JSONFileModelBase


class ParametersModel(JSONFileModelBase):
    _filename: ClassVar[str] = FileConstants.PARAMETERS_SUFFIX
    """
    A base model for parameters objects stored in JSON structure.

    This model provides two main functionalities:
    1.  A validator to automatically unpack nested data based on a 'key'
        from the subclass's Config.
    2.  A method to wrap the model's data back into the nested structure
        for serialization.
    """

    parameters: list[Parameter] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _unpack_and_validate(cls, data: Any) -> Any:
        """
        Unpacks and validates the data against the key
        specified in the subclass's Config.
        """
        if not isinstance(data, dict):
            return data

        config = getattr(cls, "Key", None)
        key = getattr(config, "key", None)

        # If there's no key in the config or the key is not in the data,
        # assume the data is already in the correct, unpacked structure.
        if not key or key not in data:
            return data

        unpacked_data = data[key]
        if not isinstance(unpacked_data, list):
            # If parameters is not a list, treat it as empty
            unpacked_data = []

        # Return data in the format expected by the model
        return {"parameters": unpacked_data}

    def model_dump_wrapped(self) -> dict[str, Any]:
        """Override to avoid double wrapping of parameters key."""
        return {"parameters": [p.model_dump() for p in self.parameters]}

    class Key:
        key = "parameters"
