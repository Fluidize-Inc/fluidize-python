"""
Node-scoped manager for user-friendly node operations.
"""

from typing import Any, Optional

from upath import UPath

from fluidize.core.constants import FileConstants
from fluidize.core.types.graph import GraphNode
from fluidize.core.types.node import nodeMetadata_simulation, nodeParameters_simulation, nodeProperties_simulation
from fluidize.core.types.parameters import Parameter
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class NodeManager:
    """
    Node manager for a specific node within a project.

    Provides node-specific operations like editing parameters, metadata,
    and properties without requiring project and node context on each method call.
    """

    def __init__(self, adapter: Any, project: ProjectSummary, node_id: str) -> None:
        """
        Initialize node-scoped manager.

        Args:
            adapter: adapter adapter (FluidizeSDK or Localadapter)
            project: The project this node belongs to
            node_id: The ID of the node this manager is bound to
        """
        self.adapter = adapter
        self.project = project
        self.node_id = node_id

    @property
    def id(self) -> str:
        """
        Get the node ID.

        Returns:
            The ID of the node this manager is bound to
        """
        return self.node_id

    @property
    def data(self) -> Any:
        """
        Get the node's data.

        Returns:
            The data of the graph node
        """
        return self.get_node().data

    def get_node(self) -> GraphNode:
        """
        Get the complete graph node data.

        Returns:
            GraphNode containing the node data

        Raises:
            ValueError: If the node is not found in the project graph
        """
        graph = self.adapter.graph.get_graph(self.project)
        for node in graph.nodes:
            if node.id == self.node_id:
                return node  # type: ignore[no-any-return]
        msg = f"Node with ID '{self.node_id}' not found in project '{self.project.id}'"
        raise ValueError(msg)

    def exists(self) -> bool:
        """
        Check if this node exists in the project graph.

        Returns:
            True if the node exists, False otherwise
        """
        try:
            self.get_node()
        except ValueError:
            return False
        else:
            return True

    def delete(self) -> None:
        """
        Delete this node from the project graph and filesystem.
        """
        self.adapter.graph.delete_node(self.project, self.node_id)

    def update_position(self, x: float, y: float) -> GraphNode:
        """
        Update the node's position in the graph.

        Args:
            x: New x coordinate
            y: New y coordinate

        Returns:
            The updated graph node
        """
        node = self.get_node()
        node.position.x = x
        node.position.y = y
        return self.adapter.graph.update_node_position(self.project, node)  # type: ignore[no-any-return]

    def get_metadata(self) -> nodeMetadata_simulation:
        """
        Get the node's metadata from metadata.yaml.

        Returns:
            The node's metadata

        Raises:
            FileNotFoundError: If metadata file doesn't exist
            ValueError: If metadata file is invalid
        """
        node_path = PathFinder.get_node_path(self.project, self.node_id)
        return nodeMetadata_simulation.from_file(node_path)

    def update_metadata(self, **kwargs: Any) -> nodeMetadata_simulation:
        """
        Update specific fields in the node's metadata.

        Args:
            **kwargs: Fields to update (e.g., name="New Name", description="New desc")

        Returns:
            The updated metadata

        Raises:
            AttributeError: If trying to update a field that doesn't exist
        """
        metadata = self.get_metadata()
        metadata.edit(**kwargs)
        return metadata

    def save_metadata(self, metadata: nodeMetadata_simulation) -> None:
        """
        Save metadata object to the node's metadata.yaml file.

        Args:
            metadata: The metadata object to save
        """
        node_path = PathFinder.get_node_path(self.project, self.node_id)
        metadata.save(node_path)

    def get_properties(self) -> nodeProperties_simulation:
        """
        Get the node's properties from properties.yaml.

        Returns:
            The node's properties

        Raises:
            FileNotFoundError: If properties file doesn't exist
            ValueError: If properties file is invalid
        """
        node_path = PathFinder.get_node_path(self.project, self.node_id)
        return nodeProperties_simulation.from_file(node_path)

    def update_properties(self, **kwargs: Any) -> nodeProperties_simulation:
        """
        Update specific fields in the node's properties.

        Args:
            **kwargs: Fields to update (e.g., container_image="new:tag", should_run=False)

        Returns:
            The updated properties

        Raises:
            AttributeError: If trying to update a field that doesn't exist
        """
        properties = self.get_properties()
        properties.edit(**kwargs)
        return properties

    def save_properties(self, properties: nodeProperties_simulation) -> None:
        """
        Save properties object to the node's properties.yaml file.

        Args:
            properties: The properties object to save
        """
        node_path = PathFinder.get_node_path(self.project, self.node_id)
        properties.save(node_path)

    def get_parameters_model(self) -> nodeParameters_simulation:
        """
        Get the node's parameters model from parameters.json.

        Returns:
            The node's parameters model

        Raises:
            FileNotFoundError: If parameters file doesn't exist
            ValueError: If parameters file is invalid
        """
        node_path = PathFinder.get_node_path(self.project, self.node_id)
        return nodeParameters_simulation.from_file(node_path)

    def get_parameters(self) -> list[Parameter]:
        """
        Get the node's parameters list from parameters.json.

        Returns:
            List of Parameter objects for the node
        """
        return self.get_parameters_model().parameters

    def get_parameter(self, name: str) -> Optional[Parameter]:
        """
        Get a specific parameter by name.

        Args:
            name: Name of the parameter to retrieve

        Returns:
            The parameter if found, None otherwise
        """
        parameters = self.get_parameters()
        for param in parameters:
            if param.name == name:
                return param
        return None

    def update_parameter(self, parameter: Parameter) -> Parameter:
        """
        Update or add a parameter.

        Args:
            parameter: The parameter to update/add

        Returns:
            The updated parameter
        """
        parameters_model = self.get_parameters_model()

        # Check if parameter with same name exists
        for p in parameters_model.parameters:
            if p.name == parameter.name:
                # Update existing parameter
                p.value = parameter.value
                p.description = parameter.description
                p.type = parameter.type
                p.label = parameter.label
                p.latex = parameter.latex
                p.options = parameter.options
                p.scope = parameter.scope
                # Handle location extension
                if parameter.location:
                    if p.location:
                        p.location.extend(parameter.location)
                    else:
                        p.location = parameter.location
                break
        else:
            # Parameter doesn't exist, add it
            parameters_model.parameters.append(parameter)

        parameters_model.save()
        return parameter

    def set_parameters(self, parameters: list[Parameter]) -> list[Parameter]:
        """
                Replace all parameters with the provided list.

                Args:
                    parameters: List of parameters to set
        W
                Returns:
                    The list of parameters that were set
        """
        parameters_model = self.get_parameters_model()
        parameters_model.parameters = parameters
        parameters_model.save()
        return parameters

    def remove_parameter(self, name: str) -> bool:
        """
        Remove a parameter by name.

        Args:
            name: Name of the parameter to remove

        Returns:
            True if parameter was removed, False if it didn't exist
        """
        parameters_model = self.get_parameters_model()
        original_count = len(parameters_model.parameters)
        parameters_model.parameters = [p for p in parameters_model.parameters if p.name != name]

        if len(parameters_model.parameters) < original_count:
            parameters_model.save()
            return True
        return False

    def show_parameters(self) -> str:
        """
        Get a formatted string display of all parameters.

        Returns:
            A formatted string displaying the parameters
        """
        parameters = self.get_parameters()

        if not parameters:
            return f"No parameters found for node '{self.node_id}'"

        output = f"Parameters for node '{self.node_id}':\n\n"

        for i, param in enumerate(parameters, 1):
            output += f"Parameter {i}:\n"
            output += f"  Name: {param.name}\n"
            output += f"  Value: {param.value}\n"
            output += f"  Description: {param.description}\n"
            output += f"  Type: {param.type}\n"
            output += f"  Label: {param.label}\n"
            if param.latex:
                output += f"  LaTeX: {param.latex}\n"
            if param.location:
                output += f"  Location: {param.location}\n"
            if param.options:
                output += f"  Options: {[opt.label for opt in param.options]}\n"
            if param.scope:
                output += f"  Scope: {param.scope}\n"
            output += "\n"

        return output

    def get_node_directory(self) -> UPath:
        """
        Get the filesystem path to this node's directory.

        Returns:
            Path to the node's directory
        """
        return PathFinder.get_node_path(self.project, self.node_id)

    def get_metadata_path(self) -> UPath:
        """
        Get the filesystem path to this node's metadata.yaml file.

        Returns:
            Path to the metadata file
        """
        return self.get_node_directory() / FileConstants.METADATA_SUFFIX

    def get_properties_path(self) -> UPath:
        """
        Get the filesystem path to this node's properties.yaml file.

        Returns:
            Path to the properties file
        """
        return PathFinder.get_properties_path(self.project, self.node_id)

    def get_parameters_path(self) -> UPath:
        """
        Get the filesystem path to this node's parameters.json file.

        Returns:
            Path to the parameters file
        """
        return PathFinder.get_node_parameters_path(self.project, self.node_id)

    def validate(self) -> dict[str, Any]:
        """
        Validate the node's files and structure.

        Returns:
            Dictionary containing validation results with keys:
            - 'valid': bool indicating if node is valid
            - 'graph_node_exists': bool
            - 'metadata_exists': bool
            - 'properties_exists': bool
            - 'parameters_exists': bool
            - 'errors': list of error messages
        """
        result: dict[str, Any] = {
            "valid": True,
            "graph_node_exists": False,
            "metadata_exists": False,
            "properties_exists": False,
            "parameters_exists": False,
            "errors": [],
        }

        # Check if node exists in graph
        try:
            self.get_node()
            result["graph_node_exists"] = True
        except ValueError as e:
            result["errors"].append(str(e))

        # Check metadata file
        try:
            self.get_metadata()
            result["metadata_exists"] = True
        except Exception as e:
            result["errors"].append(f"Metadata error: {e}")

        # Check properties file
        try:
            self.get_properties()
            result["properties_exists"] = True
        except Exception as e:
            result["errors"].append(f"Properties error: {e}")

        # Check parameters file
        try:
            self.get_parameters()
            result["parameters_exists"] = True
        except Exception as e:
            result["errors"].append(f"Parameters error: {e}")

        result["valid"] = len(result["errors"]) == 0
        return result

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the complete node information to a dictionary.

        Returns:
            Dictionary containing node graph data, metadata, properties, and parameters
        """
        try:
            return {
                "graph_node": self.get_node().model_dump(),
                "metadata": self.get_metadata().model_dump(),
                "properties": self.get_properties().model_dump(),
                "parameters": [p.model_dump() for p in self.get_parameters()],
                "paths": {
                    "node_directory": str(self.get_node_directory()),
                    "metadata_file": str(self.get_metadata_path()),
                    "properties_file": str(self.get_properties_path()),
                    "parameters_file": str(self.get_parameters_path()),
                },
            }
        except Exception as e:
            return {"error": str(e), "node_id": self.node_id, "project": self.project.id}
