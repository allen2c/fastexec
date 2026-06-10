"""
Workflow-diagram visualization (optional; requires the ``viz`` extra).

Importing this module pulls in graphviz. Core never imports it.
"""

import itertools

try:
    import graphviz
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "fastexec visualization requires the 'viz' extra: pip install fastexec[viz]"
    ) from e

import fastapi.routing

from fastexec._app import FastExec
from fastexec._routing import Router

_FILL = {
    "route": "#9ecae1",
    "dep": "#f0f0f0",
    "state": "#c7e9c0",
}
_CAPTION = "arrows follow execution order — a dependency points to what uses it"


def visualize(target, *, path=None):
    """Render a fastexec app / route / router as a workflow Digraph."""
    routes, outer_label, state_keys = _collect(target, path)

    nodes = {}  # key -> {"id", "label", "attrs"}
    edges = set()  # (child_id, parent_id)
    node_tags = {}  # key -> set(tag)
    used_markers = set()
    counter = itertools.count()

    def walk(dep, tag, is_route, route_path):
        key = dep.cache_key if dep.use_cache else ("nocache", next(counter))
        created = key not in nodes
        if created:
            nodes[key] = {
                "id": f"n{len(nodes)}",
                "label": _label(dep, is_route, route_path),
                "attrs": _attrs(dep, "route" if is_route else "dep"),
            }
            if not dep.use_cache:
                used_markers.add("nocache")
            if dep.is_async_gen_callable or dep.is_gen_callable:
                used_markers.add("yield")
        node_tags.setdefault(key, set()).add(tag)
        if created:
            for child in dep.dependencies:
                child_key = walk(child, tag, False, route_path)
                edges.add((nodes[child_key]["id"], nodes[key]["id"]))
        return key

    for route in routes:
        tag = route.tags[0] if route.tags else None
        walk(route.dependant, tag, True, route.path)

    placement, tags = _place(node_tags)

    dot = graphviz.Digraph("fastexec-workflow")
    dot.attr(label=_CAPTION, labelloc="b", fontsize="10", newrank="true")
    dot.attr("node", shape="box")

    with dot.subgraph(name="cluster_outer") as outer:
        outer.attr(label=outer_label, style="rounded", color="grey")
        if state_keys:
            outer.node(
                "fe_state",
                label="app state\n{" + ", ".join(state_keys) + "}",
                style="filled",
                fillcolor=_FILL["state"],
                shape="folder",
            )
        for key, node in nodes.items():
            if placement[key] is None:
                outer.node(node["id"], label=node["label"], **node["attrs"])
        for tag in sorted(tags):
            with outer.subgraph(name=f"cluster_tag_{tag}") as tag_c:
                tag_c.attr(label=tag, style="rounded", color="grey")
                for key, node in nodes.items():
                    if placement[key] == tag:
                        tag_c.node(node["id"], label=node["label"], **node["attrs"])

    for child_id, parent_id in edges:
        dot.edge(child_id, parent_id)

    _add_legend(dot, used_markers, bool(state_keys))
    return dot


def _collect(target, path):
    if isinstance(target, FastExec):
        all_routes = [
            r for r in target.routes if isinstance(r, fastapi.routing.APIRoute)
        ]
        if path is not None:
            routes = [r for r in all_routes if r.path == path]
            if not routes:
                raise LookupError(f"No workflow registered for path: {path}")
        else:
            routes = all_routes
        state_keys = list(getattr(target.state, "_state", {}))
        return routes, "app", state_keys
    if isinstance(target, Router):
        if path is not None:
            raise TypeError("path is only valid with a FastExec target")
        routes = [r for r in target.routes if isinstance(r, fastapi.routing.APIRoute)]
        return routes, "router", []
    raise TypeError(f"Cannot visualize {type(target).__name__}")


def _place(node_tags):
    placement = {}
    tags = set()
    for key, used in node_tags.items():
        real = {t for t in used if t is not None}
        if len(real) == 1 and None not in used:
            placement[key] = next(iter(real))
        else:
            placement[key] = None
        tags |= real
    return placement, tags


def _label(dep, is_route, route_path):
    name = getattr(dep.call, "__name__", None) or repr(dep.call)
    if is_route:
        name = f"{name}\n{route_path}"
    marks = []
    if not dep.use_cache:
        marks.append("no cache")
    if dep.is_async_gen_callable or dep.is_gen_callable:
        marks.append("yield")
    if marks:
        name = f"{name}\n({', '.join(marks)})"
    return name


def _attrs(dep, kind):
    attrs = {"style": "filled", "fillcolor": _FILL[kind]}
    if dep.is_async_gen_callable or dep.is_gen_callable:
        attrs["shape"] = "box3d"
    if not dep.use_cache:
        attrs["style"] = "filled,dashed"
    return attrs


def _add_legend(dot, used_markers, has_state):
    items = [
        ("legend_route", "route / endpoint", {"fillcolor": _FILL["route"]}),
        ("legend_dep", "dependency (node)", {"fillcolor": _FILL["dep"]}),
    ]
    if has_state:
        items.append(
            (
                "legend_state",
                "app state",
                {"fillcolor": _FILL["state"], "shape": "folder"},
            )
        )
    if "nocache" in used_markers:
        items.append(
            (
                "legend_nocache",
                "no cache\n(runs every call)",
                {"fillcolor": _FILL["dep"], "style": "filled,dashed"},
            )
        )
    if "yield" in used_markers:
        items.append(
            (
                "legend_yield",
                "yield\n(setup / teardown)",
                {"fillcolor": _FILL["dep"], "shape": "box3d"},
            )
        )
    with dot.subgraph(name="cluster_legend") as legend:
        legend.attr(label="Legend", style="rounded", color="grey", fontsize="9")
        for nid, label, attrs in items:
            attrs.setdefault("style", "filled")
            legend.node(nid, label=label, fontsize="9", margin="0.05,0.03", **attrs)
