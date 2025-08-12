class ProcessGraph:
    def print_bfs_nodes(self, G, start_node=None):
        """
        Print nodes in BFS order starting from a specific node.
        Returns two lists: one with node IDs and one with previous node IDs.

        Parameters:
        - G: NetworkX graph
        - start_node: Node to start BFS from. If None, picks the first node in the graph.

        Returns:
        - nodes: List of node IDs in BFS order
        - prev_nodes: List of previous node IDs (matching the index of nodes list)
        """

        if not G.nodes():
            print("Empty graph, no nodes to traverse.")
            return [], []

        # If no start node is provided, use the first node in the graph
        if start_node is None:
            start_node = next(iter(G.nodes()))
            print(f"No start node provided, using first node: {start_node}")

        # Check if the start node exists in the graph
        if start_node not in G:
            print(f"Start node '{start_node}' not found in graph.")
            return [], []

        print(f"BFS traversal starting from node '{start_node}':")

        # Perform BFS traversal
        visited = []
        queue = [(start_node, None)]  # (node, prev_node)
        nodes = []
        prev_nodes = []

        while queue:
            node, prev_node = queue.pop(0)  # Dequeue a vertex and its previous node from queue
            if node not in visited:
                visited.append(node)
                nodes.append(node)
                prev_nodes.append(prev_node)
                print(f"  - Adding node to traversal: {node}, previous node: {prev_node}")

                # Add all unvisited neighbors to queue
                for neighbor in G.neighbors(node):
                    if neighbor not in visited and neighbor not in [n for n, _ in queue]:
                        queue.append((neighbor, node))
                        print(f"    - Adding neighbor to queue: {neighbor}, will follow {node}")

        return nodes, prev_nodes
