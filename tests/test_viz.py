"""
Dependency-injection visualization: cache-aware DAG over the merged Dependant.
Tests assert on Digraph.source (DOT text) — no `dot` binary needed.
"""

import fastapi
import graphviz
import pytest

from fastexec import FastExec, Pipeline, viz


def _build_app():
    def get_token(request: fastapi.Request):
        return "t"

    def get_user(token: str = fastapi.Depends(get_token)):
        return "u"

    def fresh(token: str = fastapi.Depends(get_token)):
        return "f"

    async def yielder():
        yield 1

    async def app_auth(): ...

    async def pipe_log(): ...

    pipeline = Pipeline(dependencies=[fastapi.Depends(pipe_log)])

    @pipeline.register("/profile")
    async def profile(
        u1=fastapi.Depends(get_user),
        u2=fastapi.Depends(get_user),  # same dep -> shared
        f=fastapi.Depends(fresh, use_cache=False),  # not shared
        y=fastapi.Depends(yielder),  # yield dep
    ):
        return {}

    app = FastExec(dependencies=[fastapi.Depends(app_auth)])
    app.include_pipeline(pipeline, prefix="/v1")
    return app


def test_visualize_route_returns_digraph():
    app = _build_app()
    g = viz.visualize(app, path="/v1/profile")
    assert isinstance(g, graphviz.Digraph)
    # endpoint + guards present
    assert "profile" in g.source
    assert "app_auth" in g.source
    assert "pipe_log" in g.source


def test_visualize_compiles_on_demand_without_exec():
    app = _build_app()
    assert "/v1/profile" not in app._compiled  # never executed
    viz.visualize(app, path="/v1/profile")
    assert "/v1/profile" in app._compiled  # compiled by viz


def test_shared_dependency_is_deduped():
    app = _build_app()
    g = viz.visualize(app, path="/v1/profile")
    # get_user used twice + get_token shared under both get_user and fresh,
    # all use_cache=True -> each is a single node. The name appears only as a
    # node label (node ids are n0, n1, ...), so a count of 1 proves dedup.
    assert g.source.count("get_user") == 1
    assert g.source.count("get_token") == 1


def test_use_cache_false_is_distinct_and_dashed():
    app = _build_app()
    g = viz.visualize(app, path="/v1/profile")
    assert "fresh" in g.source
    assert "dashed" in g.source  # fresh node is dashed


def test_layers_are_coloured():
    app = _build_app()
    g = viz.visualize(app, path="/v1/profile")
    assert viz._LAYER_FILL["app"] in g.source  # app-guard colour
    assert viz._LAYER_FILL["pipeline"] in g.source  # pipeline-guard colour
    assert viz._LAYER_FILL["endpoint"] in g.source  # endpoint colour


def test_yield_dependency_uses_box3d():
    app = _build_app()
    g = viz.visualize(app, path="/v1/profile")
    assert "box3d" in g.source


def test_unknown_path_raises_lookuperror():
    app = _build_app()
    with pytest.raises(LookupError):
        viz.visualize(app, path="/nope")


def test_app_scope_shares_guards_across_routes():
    def app_auth(): ...

    pipeline = Pipeline()

    @pipeline.register("/alpha")
    async def route_alpha():
        return {}

    @pipeline.register("/beta")
    async def route_beta():
        return {}

    app = FastExec(dependencies=[fastapi.Depends(app_auth)])
    app.include_pipeline(pipeline)

    g = viz.visualize(app)  # whole app, two routes
    assert g.source.count("app_auth") == 1  # shared guard -> one node
    assert "route_alpha" in g.source and "route_beta" in g.source


def test_visualize_pipeline_has_no_app_guard_layer():
    async def pipe_log(): ...

    pipeline = Pipeline(dependencies=[fastapi.Depends(pipe_log)])

    @pipeline.register("/p")
    async def pipe_route():
        return {}

    g = viz.visualize(pipeline)  # pipeline in isolation
    assert "pipe_route" in g.source
    assert "pipe_log" in g.source
    # No app-level guard colour, since there is no app.
    assert viz._LAYER_FILL["app"] not in g.source


def test_path_with_pipeline_raises_typeerror():
    pipeline = Pipeline()

    @pipeline.register("/p")
    async def p():
        return {}

    with pytest.raises(TypeError):
        viz.visualize(pipeline, path="/p")
