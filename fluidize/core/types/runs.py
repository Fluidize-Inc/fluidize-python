# minor Issue : Addressing the UPath and CloudPath would be nice
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict
from upath import UPath

from .file_models.metadata_model import MetadataModel


class RunStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"


# Metadata for a project run in the metadata.yaml file.
class projectRunMetadata(MetadataModel):
    """Metadata generated for a project run."""

    metadata_version: str = "1.0"
    run_number: int
    run_folder: str
    name: str
    id: str
    date_created: str
    date_modified: Optional[str]
    description: Optional[str]
    tags: Optional[list[str]] = None
    run_status: RunStatus = RunStatus.NOT_RUN
    mlflow_run_id: Optional[str] = None
    mlflow_experiment_id: Optional[str] = None

    class Key:
        key = "run"
        metadata_version: str = "1.0"

    model_config = ConfigDict(use_enum_values=True, extra="ignore")


class NodePaths(BaseModel):
    """Paths on the host/node filesystem."""

    # This is required because UPath and CloudPath are not natively supported by Pydantic.
    model_config = ConfigDict(arbitrary_types_allowed=True)
    node_path: Union[Path, UPath]
    simulation_path: Union[Path, UPath]
    input_path: Optional[Union[Path, UPath]] = None
    output_path: Optional[Union[Path, UPath]] = None


class ContainerPaths(BaseModel):
    """Paths inside the container."""

    node_path: PurePosixPath
    simulation_path: PurePosixPath
    input_path: Optional[PurePosixPath] = None
    output_path: Optional[PurePosixPath] = None
