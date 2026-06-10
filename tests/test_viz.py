"""
Workflow-diagram visualization: cache-aware DAG in scope containers.
Tests assert on Digraph.source (DOT text) — no `dot` binary needed.
"""

import fastapi
import graphviz
import pytest

from fastexec import FastExec, Router, viz


def _build_app():
    async def app_auth(): ...

    def get_token():
        return "t"

    def get_user(token: str = fastapi.Depends(get_token)):
        return "u"

    async def db_session():
        yield "s"

    users = Router()

    @users.route("/me")
    async def me(
        u=fastapi.Depends(get_user),
        db=fastapi.Depends(db_session),
        fresh=fastapi.Depends(get_user, use_cache=False),
    ):
        return {}

    @users.route("/list")
    async def list_users(u=fastapi.Depends(get_user)):
        return []

    app = FastExec(dependencies=[fastapi.Depends(app_auth)])
    app.state.db = "x"

    @app.route("/health")
    async def health():
        return {"ok": True}

    app.include_router(users, prefix="/users", tags=["users"])
    return app


def test_visualize_app_returns_digraph():
    g = viz.visualize(_build_app())
    assert isinstance(g, graphviz.Digraph)


def test_shared_dependency_is_deduped():
    g = viz.visualize(_build_app())
    # get_token shared, get_user (cached) shared -> one node each
    assert g.source.count("get_token") == 1
    assert g.source.count("label=get_user") == 1


def test_use_cache_false_distinct_and_dashed():
    g = viz.visualize(_build_app())
    assert "no cache" in g.source
    assert "dashed" in g.source


def test_yield_dependency_box3d():
    g = viz.visualize(_build_app())
    assert "box3d" in g.source


def test_containers_app_and_tag():
    g = viz.visualize(_build_app())
    assert "subgraph cluster_outer" in g.source  # app container
    assert "subgraph cluster_tag_users" in g.source  # per-tag container


def test_app_state_node_shows_keys():
    g = viz.visualize(_build_app())
    assert "app state" in g.source
    assert "db" in g.source


def test_app_guard_lands_in_app_container_not_tag():
    # app_auth is used by tagged AND untagged routes -> app container, single node
    g = viz.visualize(_build_app())
    assert g.source.count("app_auth") == 1


def test_visualize_single_route():
    app = _build_app()
    g = viz.visualize(app, path="/health")
    assert isinstance(g, graphviz.Digraph)
    assert "health" in g.source


def test_unknown_path_raises_lookuperror():
    app = _build_app()
    with pytest.raises(LookupError):
        viz.visualize(app, path="/nope")


def test_visualize_router_has_router_container_no_app_state():
    router = Router()

    @router.route("/p")
    async def p():
        return {}

    g = viz.visualize(router)
    assert "subgraph cluster_outer" in g.source
    assert "label=router" in g.source  # outer container labelled "router"
    assert "app state" not in g.source  # no app state without an app


def test_path_with_router_raises_typeerror():
    router = Router()

    @router.route("/p")
    async def p():
        return {}

    with pytest.raises(TypeError):
        viz.visualize(router, path="/p")


def test_unsupported_target_raises_typeerror():
    with pytest.raises(TypeError):
        viz.visualize(object())


def test_legend_off_by_default():
    g = viz.visualize(_build_app())
    assert "Legend" not in g.source
    assert "cluster_legend" not in g.source


def test_legend_on_when_requested():
    g = viz.visualize(_build_app(), legend=True)
    assert "Legend" in g.source
    assert "cluster_legend" in g.source
