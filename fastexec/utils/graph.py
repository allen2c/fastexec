import pathlib
import typing

import fastapi
import fastapi.dependencies.models
import graphviz


def visualize_dependant(
    dep: fastapi.dependencies.models.Dependant,
    *,
    name: typing.Text = "Dependency Graph",
) -> graphviz.Digraph:
    # Create a new digraph with styling
    dot = graphviz.Digraph(
        comment=name,
        format="png",
        engine="dot",
        graph_attr={
            "rankdir": "TB",  # Top to bottom layout (vertical)
            "bgcolor": "#f7f7f7",  # Light gray background
            "fontname": "Arial",
            "fontsize": "12",
            "splines": "curved",  # Curved lines
            "nodesep": "0.5",  # Space between nodes
            "ranksep": "0.75",  # Space between ranks
        },
        node_attr={
            "shape": "box",
            "style": "rounded,filled",
            "fillcolor": "#e6f3ff",  # Light blue nodes (default)
            "color": "#4c7ebd",  # Border color
            "fontname": "Arial",
            "fontsize": "10",
            "height": "0.4",
            "width": "0.4",
            "penwidth": "1.0",
            "margin": "0.2,0.1",
        },
        edge_attr={
            "color": "#666666",
            "arrowsize": "0.7",
            "penwidth": "1.0",
            "fontname": "Arial",
            "fontsize": "8",
        },
    )

    visited = {}  # dictionary mapping function object to node id
    added_edges = set()  # set to track already added reversed edges (child, parent)
    parents = set()  # to track nodes that are parents
    all_nodes = set()  # to track all nodes

    # Build the starting node (path node)
    path_node_id = None
    if dep.path:
        path_node_id = "path_node"
        dot.node(
            path_node_id,
            label=str(dep.path),
            _attributes={
                "fillcolor": "#d5f5e3",  # Light green for starting node
                "color": "#2ecc71",  # Dark green border
                "fontname": "Arial Bold",
                "fontsize": "11",
            },
        )
        all_nodes.add(path_node_id)

    def add_nodes(dependant, parent_id=None):
        key = dependant.call  # use the function object as the key
        if key in visited:
            node_id = visited[key]
        else:
            label = getattr(dependant.call, "__name__", str(dependant.call))
            node_id = f"{label}_{len(visited)}"
            visited[key] = node_id
            # We'll set the color later after identifying terminal nodes
            dot.node(node_id, label=label)
            all_nodes.add(node_id)

        if parent_id is not None:
            parents.add(parent_id)
            edge = (node_id, parent_id)
            if edge not in added_edges:
                # Reverse the arrow: dependency (child) -> parent
                dot.edge(node_id, parent_id)
                added_edges.add(edge)

        for subdep in getattr(dependant, "dependencies", []):
            add_nodes(subdep, node_id)

    # Add dependencies
    add_nodes(dep)

    # If path node exists, connect it to the root dependency node
    if path_node_id and visited:
        root_node = visited.get(dep.call)
        if root_node:
            dot.edge(path_node_id, root_node)
            parents.add(path_node_id)
            added_edges.add((path_node_id, root_node))

    # Identify terminal nodes (nodes that are parents but have no children)
    terminal_nodes = parents - {src for src, _ in added_edges}

    # Update terminal nodes to have a different color
    for node_id in all_nodes:
        if node_id in terminal_nodes:
            # Terminal nodes get a different color (light orange)
            dot.node(
                node_id,
                _attributes={
                    "fillcolor": "#ffeecc",  # Light orange
                    "color": "#d4a76a",  # Darker orange border
                },
            )

    return dot


def save_dependant_graph_image(
    dep: fastapi.dependencies.models.Dependant,
    path: typing.Text | pathlib.Path,
    *,
    name: typing.Text = "Dependency Graph",
) -> pathlib.Path:
    path = pathlib.Path(path)

    # Visualize the dependency graph of the dependant function
    dot = visualize_dependant(dep, name=name)
    dot.format = "png"  # Save output as PNG image
    dot.render(path.with_suffix("") if str(path).endswith(".png") else path)

    return path
