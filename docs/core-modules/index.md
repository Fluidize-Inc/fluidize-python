# Core Modules

The Fluidize library is composed of a set of core modules that provide a high-level interface for managing Fluidize resources. These modules are designed to be used together to build and execute scientific computing pipelines.

## [Client](client.md)

The **Fluidize Client** provides a unified, high-level interface for managing Fluidize resources in both local and cloud API modes. It serves as the primary entry point for creating and running pipelines across these environments.

## [Projects](projects.md)

The **Projects** module provides tools for managing project lifecycles:

- [**Registry Manager**](projects.md#fluidize.managers.registry.RegistryManager):
  Handles the user’s complete project registry, with functionality to create, edit, and delete projects.

- [**Project Manager**](projects.md#fluidize.managers.project.ProjectManager):
  Focuses on individual projects, managing the project graph, nodes, and runs, and supporting execution of project-specific workflows.

## [Graph](graph.md)

The **Graph** module provides tools for managing the project graph, which is a representation of the simulation pipeline.

In a Fluidize project, pipelines are represented as a directed acyclic graph (DAG) where each node represents a module simulation and each edge represents the flow of data between nodes:

- [**Graph Manager**](graph.md#fluidize.managers.graph.GraphManager):
  Manages the project graph, and provides high level functionality to create, edit, and delete nodes and edges.

- [**Graph Processor**](graph.md#fluidize.managers.graph.graph_processor.GraphProcessor):
  Manages specific operations on the graph data structure within the local filesystem.

## [Node](node.md)

The **Node** module provides tools for managing the metadata, properties, and parameters of individual nodes within a project.

## [Run](run.md)

The **Run** module provides tools for managing simulation pipeline runs within a project:

- [**Runs Manager**](run.md#fluidize.managers.run.RunsManager):
  Manages the high level execution of runs and retrieving run status.

- [**Project Runner**](run.md#fluidize.core.modules.run.project.ProjectRunner):
  Manages the specific execution details of a project pipeline, including environment preparation and node execution order.
