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
    dot = graphviz.Digraph(comment=name)
    visited = {}  # dictionary mapping function object to node id
    added_edges = set()  # set to track already added reversed edges (child, parent)

    def add_nodes(dependant, parent_id=None):
        key = dependant.call  # use the function object as the key
        if key in visited:
            node_id = visited[key]
        else:
            label = getattr(dependant.call, "__name__", str(dependant.call))
            node_id = f"{label}_{len(visited)}"
            visited[key] = node_id
            dot.node(node_id, label=label)
        if parent_id is not None:
            edge = (node_id, parent_id)
            if edge not in added_edges:
                # Reverse the arrow: dependency (child) -> parent
                dot.edge(node_id, parent_id)
                added_edges.add(edge)
        for subdep in getattr(dependant, "dependencies", []):
            add_nodes(subdep, node_id)

    add_nodes(dep)
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
