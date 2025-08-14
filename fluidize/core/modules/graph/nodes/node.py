from fluidize.core.types.graph import GraphNode


def parse_node_from_json(data: dict) -> list[GraphNode]:
    # If "nodes" is missing or not a list, treat it as empty
    raw_nodes = data.get("nodes")
    if not isinstance(raw_nodes, list):
        raw_nodes = []
    return [GraphNode.model_validate(item) for item in raw_nodes]
