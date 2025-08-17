from __future__ import annotations

from typing import Any, TypeVar, Union

from pydantic import BaseModel, ConfigDict, PrivateAttr, ValidationError
from upath import UPath

T = TypeVar("T", bound="JSONFileModelBase")


class JSONFileModelBase(BaseModel):
    _filepath: Union[UPath, None] = PrivateAttr(default=None)

    @property
    def filepath(self) -> UPath:
        """Return the exact path to the model file. Raises if not set."""
        if not self._filepath:
            raise ValueError()
        return self._filepath

    @property
    def directory(self) -> UPath:
        """Return the folder containing the model file. Raises if filepath not set."""
        fp = self.filepath
        return fp.parent

    @classmethod
    def from_file(cls: type[T], directory: Union[str, UPath]) -> T:
        from fluidize.core.utils.dataloader.data_loader import DataLoader

        filename = getattr(cls, "_filename", None)
        if not filename:
            raise TypeError()

        path = UPath(directory) / filename
        data = DataLoader.load_json(path)

        if not data:
            raise FileNotFoundError()

        try:
            instance = cls.model_validate(data)
        except ValidationError:
            raise
        except Exception as e:
            raise ValueError() from e
        else:
            instance._filepath = path
            return instance

    @classmethod
    def from_dict_and_path(cls: type[T], data: dict, path: UPath) -> T:
        """Creates a model instance from a dictionary and a path, without reading the file again."""
        if not data:
            raise ValueError()

        try:
            instance = cls.model_validate(data)
        except ValidationError:
            raise
        except Exception as e:
            raise ValueError() from e
        else:
            instance._filepath = path
            return instance

    def model_dump_wrapped(self) -> dict[str, Any]:
        config = getattr(self, "Key", None)
        key = getattr(config, "key", None)

        if not key:
            return self.model_dump()

        return {key: self.model_dump(mode="json")}

    def save(self, directory: UPath | None = None) -> None:
        from fluidize.core.utils.dataloader.data_loader import DataLoader
        from fluidize.core.utils.dataloader.data_writer import DataWriter

        if directory:
            filename = getattr(self.__class__, "_filename", None)
            if not filename:
                raise TypeError()
            self._filepath = UPath(directory) / filename

        if not self._filepath:
            raise ValueError()

        # Load existing data to preserve other keys, if the file already exists.
        # Pass a new UPath object to avoid issues with object caching if it's the same file.
        existing_data = DataLoader.load_json(UPath(self._filepath))

        new_data = self.model_dump_wrapped()
        existing_data.update(new_data)

        DataWriter.write_json(self._filepath, existing_data)

    def edit(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError()
        self.save()

    model_config = ConfigDict(arbitrary_types_allowed=True)
