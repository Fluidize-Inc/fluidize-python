"""

Data Structure for graph.json file within projects.

"""

from typing import Optional

from pydantic import BaseModel


class Position(BaseModel):
    """Position of a node in layout space."""

    x: float  #: X coordinate in layout space.
    y: float  #: Y coordinate in layout space.


class graphNodeData(BaseModel):
    """Extra metadata for a node."""

    label: str  #: Node label.
    simulation_id: Optional[str] = None  #: Simulation ID.


# Default Node Type in GraphGraph
class GraphNode(BaseModel):
    """A node in the graph.

    Attributes:
        id: Unique node ID.
        position: Node position.
        data: Extra metadata.
        type: Renderer/type key.
    """

    id: str  #: Node ID.
    position: Position  #: Node position.
    data: graphNodeData  #: Node data.
    type: str  #: Node type.


# Edge Type in Graph
class GraphEdge(BaseModel):
    """An edge in the graph.

    Attributes:
        id: Unique edge ID.
        source: Source node ID.
        target: Target node ID.
        type: Renderer/type key.
    """

    id: str  #: Edge ID.
    source: str  #: Source node ID.
    target: str  #: Target node ID.
    type: str  #: Edge type.


class GraphData(BaseModel):
    """A graph representation of a project in the `graph.json` file.

    Attributes:
        nodes: List of nodes.
        edges: List of edges.
    """

    nodes: list[GraphNode]  #: List of nodes.
    edges: list[GraphEdge]  #: List of edges.
