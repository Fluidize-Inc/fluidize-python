from typing import Any

from upath import UPath

from fluidize.core.types.file_models.metadata_model import MetadataModel
from fluidize.core.types.file_models.properties_model import PropertiesModel
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.retrieval.handler import get_handler


class DataLoader:
    def __init__(self) -> None:
        pass

    @classmethod
    def _get_handler(cls) -> Any:
        return get_handler("dataloader")

    @classmethod
    def list_directories(cls, path: UPath) -> list[UPath]:
        return list(cls._get_handler().list_directories(path))

    @classmethod
    def copy_directory(cls, source: UPath, destination: UPath) -> None:
        cls._get_handler().copy_directory(source, destination)
        return None

    @classmethod
    def load_json(cls, filepath: UPath) -> dict:
        return dict(cls._get_handler().load_json(filepath))

    @classmethod
    def load_yaml(cls, filepath: UPath) -> dict:
        return dict(cls._get_handler().load_yaml(filepath))

    @classmethod
    def load_for_project(cls, project: ProjectSummary, suffix: str) -> dict:
        return dict(cls._get_handler().load_for_project(project, suffix))

    @classmethod
    def delete_directory_for_project(cls, project: ProjectSummary, folder_name: str) -> None:
        cls._get_handler().delete_directory_for_project(project, folder_name)
        return None

    @classmethod
    def delete_entire_project_folder(cls, project: ProjectSummary) -> None:
        cls._get_handler().delete_entire_project_folder(project)
        return None

    @classmethod
    def load_node_parameters(cls, path: UPath) -> dict:
        return dict(cls._get_handler().load_node_parameters(path))

    @classmethod
    def list_runs(cls, project: ProjectSummary) -> list[str]:
        return list(cls._get_handler().list_runs(project))

    @classmethod
    def list_metadatas(cls, path: UPath, objectType: type) -> list[MetadataModel]:
        return list(cls._get_handler().list_metadatas(path, objectType))

    @classmethod
    def list_properties(cls, path: UPath, objectType: type) -> list[PropertiesModel]:
        return list(cls._get_handler().list_properties(path, objectType))

    @classmethod
    def list_simulations(cls, sim_global: bool = True) -> list[Any]:
        return list(cls._get_handler().list_simulations(sim_global))

    @classmethod
    def check_file_exists(cls, filepath: UPath) -> bool:
        return bool(cls._get_handler().check_file_exists(filepath))

    @classmethod
    def remove_directory(cls, dirpath: UPath) -> None:
        cls._get_handler().remove_directory(dirpath)
        return None
