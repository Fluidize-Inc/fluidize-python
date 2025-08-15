"""

This module defines the format for files within individual nodes in the graph.
# TODO: Make more clear documentation.

"""

import datetime
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, computed_field

from .file_models.metadata_model import MetadataModel
from .file_models.properties_model import PropertiesModel
from .runs import RunStatus

# ISSUE #32
""" Properties.yaml.simulations"""


class nodeProperties_simulation(PropertiesModel):
    properties_version: str = "1.0"
    # node_id is now a computed field based on folder name (see below)
    container_image: str
    simulation_mount_path: str
    source_output_folder: str = "output"  # Where simulation creates files
    should_run: bool = True  # Add default value
    last_run: Optional[str] = None
    run_status: RunStatus = RunStatus.NOT_RUN
    version: Union[str, float] = "1.0"  # Accept both string and float

    @computed_field
    def node_id(self) -> str:
        """Node ID is always the folder name where this node exists"""
        return self.directory.name

    @computed_field
    def output_path(self) -> str:
        return str(self.directory / self.source_output_folder)

    model_config = ConfigDict(
        use_enum_values=True,  # Use enum values in serialization
        extra="ignore",  # Ignore extra fields
    )

    class Key:
        key = "simulation"
        # Extra fields won't trigger validation errors
        extra = "ignore"


""" Metadata.yaml"""
""" This file contains metadata about the node, including

name: str = display name of the node
description: str = description of the source code
version: str = version of the node
authors: list[author] = list of authors of the node
tags: list[str] = list of tags associated with the node
code_url: str = URL to the source code of the node
paper_url: Optional[str] = URL to the paper associated with the node

"""


class author(BaseModel):
    name: str
    institution: str
    email: Optional[str] = None  # Optional email field for the author


# More will be done here later
class tag(BaseModel):
    name: str
    description: Optional[str] = None  # Optional description for the tag
    color: Optional[str] = None  # Optional color for the tag, e.g., hex code
    icon: Optional[str] = None  # Optional icon for the tag, e.g., an emoji or icon name


# ISSUE #32
class nodeMetadata_simulation(MetadataModel):
    metadata_version: str = "1.0"
    name: str
    # This is the simulation ID - stays constant throughout
    id: str
    description: str
    date: Optional[datetime.date]
    version: str
    authors: list[author]
    tags: list[tag]
    code_url: Optional[str] = None
    paper_url: Optional[str] = None
    mlflow_run_id: Optional[str] = None

    class Key:
        key = "simulation"
        metadata_version = "1.0"
