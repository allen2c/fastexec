# Visualization

Render a dependency-injection graph for a route, a pipeline, or the whole app.
Requires the `viz` extra **and** a system Graphviz install (the `dot` binary).

```bash
pip install fastexec[viz]      # Python wrapper
brew install graphviz          # macOS — the `dot` renderer
# Debian/Ubuntu: apt install graphviz
```

```python
from fastexec import viz

g = viz.visualize(app)                  # whole app
g = viz.visualize(app, path="/v1/x")    # one route
g = viz.visualize(pipeline)             # a pipeline in isolation (no app guards)

g                                       # auto-renders as SVG in Jupyter
g.render("deps", format="svg")          # write deps.svg
g.pipe(format="png")                    # PNG bytes
```

## What the graph shows

The graph is **cache-aware** — it reflects how dependencies actually execute, not
just how they are declared:

- A dependency shared by several consumers is drawn **once**, with one edge per
  consumer (FastAPI caches it per request and runs it once).
- A `Depends(..., use_cache=False)` dependency is drawn as a **separate, dashed**
  node — it runs at every use.
- Nodes are coloured by layer: endpoint, app-guard, pipeline-guard, and plain
  dependencies. Yield dependencies (with setup/teardown) use a `box3d` shape.

`visualize(pipeline)` shows the pipeline in isolation, so it has no app-guard
layer — those belong to the `FastExec` app.
