"""

Data Structure for graph.json file within projects.

"""

from pydantic import BaseModel


class Position(BaseModel):
    x: float
    y: float


class graphNodeData(BaseModel):
    label: str
    simulation_id: str


# Default Node Type in Graph
class GraphNode(BaseModel):
    id: str
    position: Position
    data: graphNodeData
    type: str


# Edge Type in Graph
class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
