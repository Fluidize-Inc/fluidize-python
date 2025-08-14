from fluidize.core.types.graph import GraphEdge


def parse_edge_from_json(data: dict) -> list[GraphEdge]:
    # If "edges" is missing or not a list, treat it as empty
    raw_edges = data.get("edges")
    if not isinstance(raw_edges, list):
        raw_edges = []
    return [GraphEdge.model_validate(item) for item in raw_edges]


# ISSUE #8
