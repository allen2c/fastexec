"""
Dependency-injection visualization (optional; requires the ``viz`` extra).

Importing this module pulls in graphviz. Core never imports it.
"""

import itertools

try:
    import graphviz
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "fastexec visualization requires the 'viz' extra: pip install fastexec[viz]"
    ) from e

from fastexec._exec import FastExec

_LAYER_FILL = {
    "endpoint": "#9ecae1",
    "app": "#fc9272",
    "pipeline": "#fdd0a2",
    "dep": "#f0f0f0",
}
_LEGEND = (
    "layers: endpoint / app-guard / pipeline-guard / dep  ·  "
    "dashed = use_cache=False  ·  box3d = yield dependency"
)


def visualize(target, *, path=None):
    """Render a fastexec app / pipeline / route's DI graph as a Digraph."""
    roots = _collect_roots(target, path)
    dot = graphviz.Digraph("fastexec-dependencies")
    dot.attr(label=_LEGEND, labelloc="b", fontsize="10")
    dot.attr("node", shape="box")
    nodes = {}
    edges = set()
    counter = itertools.count()
    for root, n_app, n_pipe in roots:
        _add_root(dot, root, n_app, n_pipe, nodes, edges, counter)
    return dot


def _collect_roots(target, path):
    if isinstance(target, FastExec):
        app = target
        if path is not None:
            return [_root_tuple(app, path)]
        return [_root_tuple(app, p) for p in app._routes]
    raise TypeError(f"Cannot visualize {type(target).__name__}")


def _root_tuple(app, path):
    if path not in app._routes:
        raise LookupError(f"No endpoint registered for path: {path}")
    if path not in app._compiled:
        app._compiled[path] = app._compile_route(path, app._routes[path])
    dependant = app._compiled[path].dependant
    return (
        dependant,
        len(app.dependencies),
        len(app._routes[path].pipeline_dependencies),
    )


def _add_root(dot, root, n_app, n_pipe, nodes, edges, counter):
    root_id, _ = _ensure_node(dot, root, "endpoint", nodes, counter)
    for i, child in enumerate(root.dependencies):
        if i < n_app:
            layer = "app"
        elif i < n_app + n_pipe:
            layer = "pipeline"
        else:
            layer = "dep"
        child_id = _add_subtree(dot, child, layer, nodes, edges, counter)
        _add_edge(dot, root_id, child_id, edges)
    return root_id


def _add_subtree(dot, dep, layer, nodes, edges, counter):
    node_id, created = _ensure_node(dot, dep, layer, nodes, counter)
    if created:
        for child in dep.dependencies:
            child_id = _add_subtree(dot, child, "dep", nodes, edges, counter)
            _add_edge(dot, node_id, child_id, edges)
    return node_id


def _ensure_node(dot, dep, layer, nodes, counter):
    key = _node_key(dep, counter)
    if key in nodes:
        return nodes[key], False
    node_id = f"n{len(nodes)}"
    nodes[key] = node_id
    dot.node(node_id, label=_label(dep), **_node_attrs(dep, layer))
    return node_id, True


def _node_key(dep, counter):
    if dep.use_cache:
        return dep.cache_key
    return ("nocache", next(counter))


def _label(dep):
    return getattr(dep.call, "__name__", None) or repr(dep.call)


def _node_attrs(dep, layer):
    attrs = {
        "style": "filled",
        "fillcolor": _LAYER_FILL.get(layer, _LAYER_FILL["dep"]),
    }
    if dep.is_async_gen_callable or dep.is_gen_callable:
        attrs["shape"] = "box3d"
    if not dep.use_cache:
        attrs["style"] = "filled,dashed"
    return attrs


def _add_edge(dot, parent_id, child_id, edges):
    edge = (parent_id, child_id)
    if edge not in edges:
        edges.add(edge)
        dot.edge(parent_id, child_id)
