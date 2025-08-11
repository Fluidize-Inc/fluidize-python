#!/usr/bin/env python3
"""
Demo script showing the new user-friendly graph API.

This demonstrates how the new Project wrapper with .graph property
makes working with project graphs much more intuitive.
"""

from fluidize import FluidizeClient
from fluidize.core.types.graph import GraphNode


def demo_new_graph_api():
    """Demonstrate the new user-friendly graph API."""

    # Initialize client
    client = FluidizeClient(mode="local")

    # Create or get a project
    project = client.projects.create(
        project_id="demo_project", label="Demo Project", description="Testing the new graph API"
    )

    print(f"Working with: {project}")
    print(f"Project ID: {project.id}")
    print(f"Project Label: {project.label}")

    # NEW USER-FRIENDLY API: Access graph operations directly on project
    print("\n=== Getting project graph ===")
    graph_data = project.graph.get()
    print(f"Current graph has {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges")

    # NEW USER-FRIENDLY API: Add a node without passing project context
    print("\n=== Adding a node ===")
    from fluidize.core.types.graph import Position, graphNodeData

    node_data = graphNodeData(label="Test Node", simulation_id="test-sim-001")
    position = Position(x=100.0, y=200.0)

    new_node = GraphNode(id="test_node_1", position=position, data=node_data, type="simulation")

    # This is much cleaner than: backend.graph.insert_node(project_summary, node)
    added_node = project.graph.add_node(new_node)
    print(f"Added node: {added_node.id} at ({added_node.position.x}, {added_node.position.y})")

    # NEW USER-FRIENDLY API: Check updated graph
    print("\n=== Updated graph ===")
    updated_graph = project.graph.get()
    print(f"Graph now has {len(updated_graph.nodes)} nodes and {len(updated_graph.edges)} edges")

    for node in updated_graph.nodes:
        print(f"  - Node {node.id}: {node.data.label} at ({node.position.x}, {node.position.y})")

    print("\n=== API Benefits ===")
    print("✅ Clean, intuitive API: project.graph.add_node()")
    print("✅ No need to pass project context repeatedly")
    print("✅ Automatic graph initialization")
    print("✅ Project-scoped operations")
    print("✅ Maintains compatibility with existing backend")


if __name__ == "__main__":
    try:
        demo_new_graph_api()
        print("\n🎉 Demo completed successfully!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
