import shutil
from pathlib import Path

from upath import UPath

from fluidize.core.utils.retrieval.handler import register_handler

from .loader_base import BaseDataLoader


class LocalDataLoader(BaseDataLoader):
    """
    Local filesystem implementation of the JSON data loader.
    """

    def _get_file_content(self, filepath: Path) -> str:
        """Load raw file content from the local filesystem as a string."""
        with open(filepath, encoding="utf-8") as f:
            return f.read()

    def _file_exists(self, filepath: Path) -> bool:
        """Check if a file exists in the local filesystem."""
        return filepath.exists() and filepath.is_file()

    def _directory_exists(self, dirpath: Path) -> bool:
        """Check if a directory exists in the local filesystem."""
        return dirpath.exists() and dirpath.is_dir()

    def _list_directory(self, dirpath: Path) -> list[UPath]:
        """List contents of a directory in the local filesystem."""
        return [UPath(item) for item in dirpath.iterdir()]

    def _is_directory(self, path: Path) -> bool:
        """Check if a path is a directory in the local filesystem."""
        return path.is_dir()

    def copy_directory(self, source: Path, destination: Path) -> None:
        """Copy a directory in the local filesystem."""
        shutil.copytree(source, destination)

    def remove_directory(self, dirpath: Path) -> None:
        """Remove a directory in the local filesystem."""
        shutil.rmtree(dirpath)

    def _create_directory(self, dirpath: Path) -> None:
        """Create a directory in the local filesystem."""
        dirpath.mkdir(parents=True, exist_ok=True)

    def _glob(self, path: Path, pattern: str) -> list[UPath]:
        """List files matching `pattern` under the given path on local filesystem."""
        return [UPath(p) for p in path.glob(pattern)]

    def _cat_files(self, paths: list[UPath]) -> dict[str, bytes]:
        """Read multiple files' content in a batch from the local filesystem."""
        contents = {}
        for path in paths:
            try:
                # UPath objects from local glob will have a 'path' attribute that is a Path object
                with open(path, "rb") as f:
                    # Use the string representation of the path as the key for consistency
                    contents[str(path)] = f.read()
            except FileNotFoundError:
                # Handle cases where a file might disappear between glob and read
                # Skip files that can't be read instead of adding None values
                continue
            except Exception as e:
                # Handle other potential reading errors
                print(f"Error reading file {path}: {e}")
                # Skip files that can't be read instead of adding None values
                continue
        return contents


# Auto-register this handler when module is imported
register_handler("dataloader", "local", LocalDataLoader)
