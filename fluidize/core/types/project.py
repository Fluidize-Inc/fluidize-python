from .file_models.metadata_model import MetadataModel

# ISSUE 17: ADDING MORE PROPERTIES TO PROJECT SUMMARY

""" This is the ProjectSummary that is used to communicate back and forth with the frontend.
This is somewhat legacy and all the YAML properties based operations are deal with in ProjectMetadata.

"""

# ISSUE 19 (IMPORTANT)


class ProjectSummary(MetadataModel):
    metadata_version: str = "1.0"
    id: str
    label: str = ""
    description: str = ""
    status: str = ""
    location: str = ""

    class Key:
        key: str = "project"
        metadata_version: str = "1.0"
