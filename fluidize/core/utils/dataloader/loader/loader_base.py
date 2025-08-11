import json
import logging
from abc import ABC, abstractmethod

import yaml
from upath import UPath

from fluidize.core.types.file_models.metadata_model import MetadataModel
from fluidize.core.types.file_models.properties_model import PropertiesModel
from fluidize.core.types.node import nodeMetadata_simulation
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class BaseDataLoader(ABC):
    """
    Base class for all data loaders. Provides shared implementation logic with
    abstract methods for file system operations that differ between local and remote.
    """

    @abstractmethod
    def _get_file_content(self, filepath: UPath) -> str:
        """Load raw file content from the given path as a string."""
        pass

    @abstractmethod
    def _file_exists(self, filepath: UPath) -> bool:
        """Check if a file exists at the given path."""
        pass

    @abstractmethod
    def _directory_exists(self, dirpath: UPath) -> bool:
        """Check if a directory exists at the given path."""
        pass

    @abstractmethod
    def _list_directory(self, dirpath: UPath) -> list[UPath]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def _is_directory(self, path: UPath) -> bool:
        """Check if a path is a directory."""
        pass

    @abstractmethod
    def _create_directory(self, dirpath: UPath) -> None:
        """Create a directory."""
        pass

    @abstractmethod
    def _glob(self, path: UPath, pattern: str) -> list[UPath]:
        """List files matching `pattern` under the given path."""
        pass

    @abstractmethod
    def _cat_files(self, paths: list[UPath]) -> dict:
        """Read multiple files' content in a batch."""
        pass

    @abstractmethod
    def copy_directory(self, source: UPath, destination: UPath) -> None:
        """Copy a directory from source to destination."""
        pass

    @abstractmethod
    def remove_directory(self, dirpath: UPath) -> None:
        """Remove a directory."""
        pass

    def check_file_exists(self, filepath: UPath) -> bool:
        """
        Check if a file exists at the given path.
        """
        return self._file_exists(filepath)

    def list_directories(self, path: UPath) -> list[UPath]:
        """
        List all folders within a given directory
        """
        return [item for item in self._list_directory(path) if self._is_directory(item)]

    def load_json(self, filepath: UPath) -> dict:
        """
        Loads JSON from the appropriate path.
        """
        if not self._file_exists(filepath):
            return {}
        try:
            content = self._get_file_content(filepath)
            return json.loads(content)
        except Exception:
            return {}

    def load_yaml(self, filepath: UPath) -> dict:
        """
        Loads YAML from the appropriate path. Returns an empty dict if file doesn't exist or is invalid.
        """
        if not self._file_exists(filepath):
            return {}
        try:
            content = self._get_file_content(filepath)
            return yaml.safe_load(content) or {}
        except Exception:
            return {}

    def load_for_project(self, project: ProjectSummary, suffix: str) -> dict:
        """
        Loads JSON for a specific project from different suffix that indicate the file. This is usually just used to load the graph.json file at the moment.
        """
        full_path = PathFinder.get_project_path(project) / suffix
        return self.load_json(full_path)

    def delete_directory_for_project(self, project: ProjectSummary, folder_name: str):
        """Delete a directory from a project folder."""
        path = PathFinder.get_project_path(project) / folder_name

        if self._directory_exists(path):
            self.remove_directory(path)

    def delete_entire_project_folder(self, project: ProjectSummary):
        """Delete the entire project folder."""
        path = PathFinder.get_project_path(project)

        if self._directory_exists(path):
            self.remove_directory(path)
            print(f"Deleted project folder: {path}")

    # ISSUE 21: THE PARAMETER LOADING PROCESS MUST BE UPDATED!
    def load_node_parameters(self, path: UPath) -> dict:
        """Load parameters for a specific node."""
        parameters_path = path / "parameters.json"

        if not self._file_exists(parameters_path):
            raise FileNotFoundError()

        content = self._get_file_content(parameters_path)
        return json.loads(content)

    def list_runs(self, project: ProjectSummary) -> list[str]:
        """List all runs for a project."""
        run_path = PathFinder.get_runs_path(project)

        if not self._directory_exists(run_path):
            return []

        runs = []
        for path in self._list_directory(run_path):
            if self._is_directory(path):
                runs.append(path.name)

        return runs

    def list_metadatas(self, path: UPath, objectType: type[MetadataModel]) -> list[MetadataModel]:
        """
        Efficiently load all objects of type `objectType` by finding all metadata files
        and reading them in a single batch.
        """
        filename = getattr(objectType, "_filename", None)
        if not filename:
            raise TypeError()

        # 1. Find all metadata files in a single, efficient glob operation
        metadata_files = self._glob(path, f"**/{filename}")
        if not metadata_files:
            return []

        # 2. Read all file contents in a single batch operation
        file_contents = self._cat_files(metadata_files)

        # 3. Create model instances from the loaded data
        objects: list[MetadataModel] = []
        for file_path_str, content_bytes in file_contents.items():
            try:
                file_path = UPath(file_path_str)
                data = yaml.safe_load(content_bytes)
                # Use the new classmethod to avoid re-reading the file
                obj = objectType.from_dict_and_path(data, file_path)
                objects.append(obj)
            except Exception as e:
                # Skip entries that are invalid
                logging.debug(f"Skipping invalid entry {file_path_str}: {e}")
                continue

        return objects

    def list_properties(self, path: UPath, objectType: type) -> list[PropertiesModel]:
        """
        Load all objects of type `objectType` by reading each folder's properties via from_file.
        """
        objects: list[PropertiesModel] = []
        try:
            # List all subdirectories under the given path
            dirs = self.list_directories(path)
        except Exception:
            return []

        for directory in dirs:
            try:
                # Use from_file to load and validate properties for each directory
                obj = objectType.from_file(directory)
                objects.append(obj)
            except Exception as e:
                # Skip entries without valid properties
                logging.debug(f"Skipping directory without valid properties {directory}: {e}")
                continue

        return objects

    def list_simulations(self, sim_global: bool = True):
        """Load all simulations by reading each folder's metadata.yaml"""
        return self.list_metadatas(PathFinder.get_simulations_path(sim_global), nodeMetadata_simulation)
