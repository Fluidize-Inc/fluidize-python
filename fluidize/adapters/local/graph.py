"""
Local filesystem-based graph adapter interface.

This module provides the local adapter interface for graph operations,
wrapping the core GraphProcessor with adapter-specific functionality.
"""

from typing import Optional

from fluidize.core.modules.graph.parameters import parse_parameters_from_json
from fluidize.core.modules.graph.processor import GraphProcessor
from fluidize.core.types.graph import GraphData, GraphEdge, GraphNode
from fluidize.core.types.node import nodeMetadata_simulation, nodeProperties_simulation
from fluidize.core.types.parameters import Parameter
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.dataloader.data_loader import DataLoader
from fluidize.core.utils.dataloader.data_writer import DataWriter
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class GraphHandler:
    """
    Local filesystem-based graph processor adapter.

    This class provides a clean interface for graph operations using the local adapter,
    wrapping the core GraphProcessor functionality.
    """

    def __init__(self) -> None:
        """Initialize the local graph processor."""
        pass

    def get_graph(self, project: ProjectSummary) -> GraphData:
        """
        Get the complete graph for a project.

        Args:
            project: The project to get the graph for

        Returns:
            GraphData containing all nodes and edges
        """
        processor = GraphProcessor(project)
        return processor.get_graph()

    def insert_node(self, project: ProjectSummary, node: GraphNode, sim_global: bool = True) -> GraphNode:
        """
        Insert a new node into the project graph.

        Args:
            project: The project to add the node to
            node: The node to insert
            sim_global: Whether to use global simulations (placeholder for future)

        Returns:
            The inserted node
        """
        processor = GraphProcessor(project)
        return processor.insert_node(node, sim_global)

    def insert_node_from_scratch(
        self,
        project: ProjectSummary,
        GraphNode: GraphNode,
        nodeProperties: nodeProperties_simulation,
        nodeMetadata: nodeMetadata_simulation,
        repo_link: Optional[str] = None,
    ) -> GraphNode:
        """
        Insert a new node into the project graph from scratch.

        Args:
            project: The project to add the node to
            nodeProperties: The properties of the node to insert
            sim_global: Whether to use global simulations (placeholder for future)

        Returns:
            The inserted node
        """
        processor = GraphProcessor(project)
        return processor.insert_node_from_scratch(GraphNode, nodeProperties, nodeMetadata, repo_link)

    def update_node_position(self, project: ProjectSummary, node: GraphNode) -> GraphNode:
        """
        Update a node's position in the graph.

        Args:
            project: The project containing the node
            node: The node with updated position

        Returns:
            The updated node
        """
        processor = GraphProcessor(project)
        return processor.update_node_position(node)

    def delete_node(self, project: ProjectSummary, node_id: str) -> None:
        """
        Delete a node from the project graph.

        Args:
            project: The project containing the node
            node_id: ID of the node to delete
        """
        processor = GraphProcessor(project)
        processor.delete_node(node_id)

    def upsert_edge(self, project: ProjectSummary, edge: GraphEdge) -> GraphEdge:
        """
        Add or update an edge in the project graph.

        Args:
            project: The project containing the graph
            edge: The edge to upsert

        Returns:
            The upserted edge
        """
        processor = GraphProcessor(project)
        return processor.upsert_edge(edge)

    def delete_edge(self, project: ProjectSummary, edge_id: str) -> None:
        """
        Delete an edge from the project graph.

        Args:
            project: The project containing the edge
            edge_id: ID of the edge to delete
        """
        processor = GraphProcessor(project)
        processor.delete_edge(edge_id)

    def ensure_graph_initialized(self, project: ProjectSummary) -> None:
        """
        Ensure the project has a graph.json file initialized.

        Args:
            project: The project to initialize the graph for
        """
        processor = GraphProcessor(project)
        processor._ensure_graph_file_exists()

    def show_graph_ascii(self, project: ProjectSummary) -> str:
        """
        Get ASCII representation of the project graph.

        Args:
            project: The project to visualize

        Returns:
            ASCII string representation of the graph
        """
        processor = GraphProcessor(project)
        graph_data = processor.get_graph()

        # Create Graph model from the data to use ASCII visualization
        from fluidize.core.modules.graph.model import Graph

        graph = Graph(nodes=graph_data.nodes, edges=graph_data.edges)

        return graph.to_ascii()

    def get_parameters(self, project: ProjectSummary, node_id: str) -> list[Parameter]:
        """
        Get the parameters for a specific node in the project graph.

        Args:
            project: The project containing the graph
            node_id: ID of the node to retrieve parameters for

        Returns:
            A list of Parameter objects for the node
        """
        parameters_path = PathFinder.get_node_parameters_path(project, node_id)
        data = DataLoader.load_json(parameters_path)
        return parse_parameters_from_json(data)

    def upsert_parameter(self, project: ProjectSummary, node_id: str, parameter: Parameter) -> Parameter:
        """
        Upsert a parameter for a specific node in the project graph.

        Args:
            project: The project containing the graph
            node_id: ID of the node to update parameters for
            parameter: The parameter to upsert

        Returns:
            The upserted parameter
        """
        parameters_path = PathFinder.get_node_parameters_path(project, node_id)
        data = DataLoader.load_json(parameters_path)
        params = parse_parameters_from_json(data)

        # Check if parameter with same name exists
        for p in params:
            if p.name == parameter.name:
                # Update the existing parameter with new values
                p.value = parameter.value
                p.description = parameter.description
                p.type = parameter.type
                p.label = parameter.label
                p.latex = parameter.latex
                p.options = parameter.options
                p.scope = parameter.scope
                # Extend the location if it exists
                if parameter.location:
                    if p.location:
                        p.location.extend(parameter.location)
                    else:
                        p.location = parameter.location
                break
        else:
            # Parameter doesn't exist, add it
            params.append(parameter)

        # Write updated parameters back
        DataWriter.write_json(
            filepath=parameters_path,
            data={"parameters": [p.model_dump() for p in params]},
        )
        return parameter

    def set_parameters(self, project: ProjectSummary, node_id: str, parameters: list[Parameter]) -> list[Parameter]:
        """
        Set all parameters for a specific node in the project graph, replacing existing ones.

        Args:
            project: The project containing the graph
            node_id: ID of the node to set parameters for
            parameters: List of parameters to set

        Returns:
            The list of parameters that were set
        """
        parameters_path = PathFinder.get_node_parameters_path(project, node_id)
        data = {"parameters": [p.model_dump() for p in parameters]}

        DataWriter.write_json(filepath=parameters_path, data=data)
        return parameters

    def show_parameters(self, project: ProjectSummary, node_id: str) -> str:
        """
        Get a nicely formatted string display of parameters for a specific node.

        Args:
            project: The project containing the graph
            node_id: ID of the node to retrieve parameters for

        Returns:
            A formatted string displaying the parameters
        """
        parameters = self.get_parameters(project, node_id)

        if not parameters:
            return f"No parameters found for node '{node_id}'"

        output = f"Parameters for node '{node_id}':\n\n"

        for i, param in enumerate(parameters, 1):
            output += f"Parameter {i}:\n"
            output += f"  Name: {param.name}\n"
            output += f"  Value: {param.value}\n"
            output += f"  Description: {param.description}\n"
            output += f"  Type: {param.type}\n"
            output += f"  Label: {param.label}\n"

            if param.scope:
                output += f"  Scope: {param.scope}\n"

            if param.location:
                output += f"  Location: {', '.join(param.location)}\n"

            if param.latex:
                output += f"  LaTeX: {param.latex}\n"

            if param.options:
                output += f"  Options: {[f'{opt.label} ({opt.value})' for opt in param.options]}\n"

            output += "\n"

        return output.rstrip()
