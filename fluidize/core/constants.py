"""
Immutable constants for Fluidize file structure and naming conventions.

These constants define the Fluidize specification and should NEVER be changed
as they ensure compatibility across all Fluidize implementations.
"""


class FileConstants:
    """Immutable file naming standards for Fluidize."""

    # Core file suffixes
    GRAPH_SUFFIX = "graph.json"
    PARAMETERS_SUFFIX = "parameters.json"
    METADATA_SUFFIX = "metadata.yaml"
    PROPERTIES_SUFFIX = "properties.yaml"
    SIMULATIONS_SUFFIX = "simulations.json"
    RETRIEVAL_MODE_SUFFIX = "retrieval_mode.json"

    # Directory structure standards
    RUNS_DIR = "runs"
    OUTPUTS_DIR = "outputs"
    SIMULATIONS_DIR = "simulations"
    PROJECTS_DIR = "projects"

    # Run naming convention
    RUN_PREFIX = "run_"

    # File encoding
    DEFAULT_ENCODING = "utf-8"
