from typing import Any, ClassVar

from pydantic import model_validator

from fluidize.core.constants import FileConstants

from .file_model_base import FileModelBase


# TODO: Think about combining the metadata_model and properties_model somehow? Separated just in case
class PropertiesModel(FileModelBase):
    _filename: ClassVar[str] = FileConstants.PROPERTIES_SUFFIX
    """
    A base model for properties objects stored in a nested structure.

    This model provides two main functionalities:
    1.  A validator to automatically unpack nested data based on a 'key'
        and validate its version from the subclass's Config.
    2.  A method to wrap the model's data back into the nested structure
        for serialization.
    """

    @model_validator(mode="before")
    @classmethod
    def _unpack_and_validate(cls, data: Any) -> Any:
        """
        Unpacks and validates the data against the key and version
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
        if not isinstance(unpacked_data, dict):
            raise TypeError()

        # If an expected version is defined in the config, validate or inject it.
        expected_version = getattr(config, "metadata_version", None)
        if expected_version is not None:
            # If the file has a version, it must match.
            if "metadata_version" in unpacked_data:
                file_version = unpacked_data.get("metadata_version")
                if file_version != expected_version:
                    raise ValueError()
            # If the file has no version, inject the expected one.
            else:
                unpacked_data["metadata_version"] = expected_version

        return unpacked_data

    # def edit_value(self, attr: str, value: Any) -> "PropertiesModel":
    #     """
    #     Update one field on this model and re-validate the assignment.
    #     Raises AttributeError if `attr` is not present.
    #     """
    #     if not hasattr(self, attr):
    #         raise AttributeError(f"{self.__class__.__name__} has no attribute {attr!r}")
    #     setattr(self, attr, value)  # will be validated thanks to validate_assignment
    #     return self
