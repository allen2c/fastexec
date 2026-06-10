# Visualization

Render a **workflow diagram** for an app, a single route, or a router.
Requires the `viz` extra **and** a system Graphviz install (the `dot` binary).

```bash
pip install fastexec[viz]      # Python wrapper
brew install graphviz          # macOS — the `dot` renderer
# Debian/Ubuntu: apt install graphviz
```

```python
from fastexec import viz

g = viz.visualize(app)                    # whole app
g = viz.visualize(app, path="/users/me")  # one route
g = viz.visualize(router)                 # a router in isolation

g                          # auto-renders as SVG in Jupyter
g.render("workflow", format="svg")        # write workflow.svg
g.pipe(format="png")                      # PNG bytes
```

## What the diagram shows

- The dependency graph is the workflow DAG. **Arrows follow execution order** — a
  dependency points to what uses its result (leaf nodes resolve first).
- It is **cache-aware**: a dependency shared by several nodes is drawn once
  (FastAPI memoizes it per run); a `Depends(..., use_cache=False)` node is drawn
  distinct and **dashed**; a `yield` dependency uses a `box3d` shape.
- Nodes are grouped into **scope containers**: the app container holds app state
  and app-wide nodes; routes tagged with FastAPI **tags** group into per-tag
  sub-containers. A node used across tags (e.g. an app-level dependency) sits in
  the app container; a tag-exclusive node sits in its tag container.

Add tags the FastAPI way to get sub-containers, e.g.
`app.include_router(router, prefix="/users", tags=["users"])`.
