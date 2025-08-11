import json

import yaml
from upath import UPath

from fluidize.core.utils.retrieval.handler import register_handler

from .writer_base import BaseDataWriter


class LocalDataWriter(BaseDataWriter):
    """
    JSON Data Writer for local filesystem storage.
    Implements primitive operations required by the base class.
    """

    def _ensure_directory_exists(self, dir_path: UPath) -> bool:
        """
        Ensures that the specified directory exists.
        Creates it if it doesn't exist.
        """
        try:
            # create directory directly on UPath
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            return False
        else:
            return True

    def _write_json_file(self, file_path: UPath, data: dict) -> bool:
        """
        Writes JSON data to the specified file path.
        """
        try:
            with file_path.open("w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error writing JSON to {file_path}: {e}")
            return False
        else:
            return True

    def _write_text_file(self, file_path: UPath, data: str) -> bool:
        try:
            with file_path.open("w") as f:
                f.write(data)
        except Exception as e:
            print(f"Error writing text to {file_path}: {e}")
            return False
        else:
            return True

    def _write_yaml(self, file_path: UPath, data: dict) -> bool:
        with file_path.open("w") as f:
            try:
                yaml.dump(data, f, default_flow_style=False)
            except Exception as e:
                print(f"Error writing YAML to {file_path}: {e}")
                return False
            else:
                return True


# Auto-register this handler when module is imported
register_handler("datawriter", "local", LocalDataWriter)
