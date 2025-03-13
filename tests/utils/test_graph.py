import pathlib
import tempfile

import fastapi
import graphviz

from fastexec import get_dependant
from fastexec.utils.graph import save_dependant_graph_image, visualize_dependant


def test_visualize_dependant_simple():
    # Setup a simple dependency
    def sample_dependency():
        return "sample"

    # Get dependant
    dependant = get_dependant(call=sample_dependency)

    # Test visualization
    graph = visualize_dependant(dependant)

    # Assert we got a proper Digraph object
    assert isinstance(graph, graphviz.Digraph)

    # Convert to source to check nodes and edges
    source = graph.source

    # Check node is present
    assert "sample_dependency" in source


def test_visualize_dependant_with_path():
    # Setup a simple dependency
    def sample_dependency():
        return "sample"

    # Get dependant with explicit path
    dependant = get_dependant(path="/test-path", call=sample_dependency)

    # Test visualization
    graph = visualize_dependant(dependant)

    # Assert path node exists
    source = graph.source
    assert "/test-path" in source


def test_visualize_dependant_complex():
    # Setup dependencies
    def dep_level3():
        return "level3"

    def dep_level2a(l3: str = fastapi.Depends(dep_level3)):
        return f"level2a with {l3}"

    def dep_level2b(l3: str = fastapi.Depends(dep_level3)):
        return f"level2b with {l3}"

    def dep_level1(
        l2a: str = fastapi.Depends(dep_level2a), l2b: str = fastapi.Depends(dep_level2b)
    ):
        return f"level1 with {l2a} and {l2b}"

    # Create dependant
    dependant = get_dependant(call=dep_level1)

    # Test visualization
    graph = visualize_dependant(dependant, name="Test Graph")

    # Assert we got a proper Digraph object
    assert isinstance(graph, graphviz.Digraph)
    assert graph.comment == "Test Graph"

    # Check graph has expected attributes
    assert graph.graph_attr["rankdir"] == "TB"
    assert graph.graph_attr["bgcolor"] == "#f7f7f7"

    # Convert to source to check nodes and edges
    source = graph.source

    # Check nodes are present (names might have suffixes)
    assert "dep_level1" in source
    assert "dep_level2a" in source
    assert "dep_level2b" in source
    assert "dep_level3" in source

    # Check for at least some edges between nodes
    # Note: This is checking for arrows in the dot syntax
    assert "->" in source


def test_save_dependant_graph_image():
    # Setup a simple dependency
    def sample_dependency():
        return "sample"

    # Get dependant
    dependant = get_dependant(call=sample_dependency)

    # Save to a temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir) / "test_graph.png"

        # Test saving
        result_path = save_dependant_graph_image(
            dependant, tmp_path, name="Test Save Graph"
        )

        # Check the function returns the input path
        assert result_path == tmp_path

        # Check at least one file was created in the directory
        files = list(pathlib.Path(tmpdir).glob("*"))
        assert len(files) > 0, "No files were created"

        # Check at least one PNG file exists
        png_files = list(pathlib.Path(tmpdir).glob("*.png"))
        assert len(png_files) > 0, "No PNG files were created"


def test_save_dependant_graph_image_no_suffix():
    # Test with path not ending in .png
    def sample_dependency():
        return "sample"

    dependant = get_dependant(call=sample_dependency)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir) / "test_graph"

        # Test saving
        result_path = save_dependant_graph_image(dependant, tmp_path)

        # Check the function returns the input path
        assert result_path == tmp_path

        # Check at least one file was created in the directory
        files = list(pathlib.Path(tmpdir).glob("*"))
        assert len(files) > 0, "No files were created"

        # Check at least one PNG file exists
        png_files = list(pathlib.Path(tmpdir).glob("*.png"))
        assert len(png_files) > 0, "No PNG files were created"
