"""Packaging sanity checks (RP-001 "done when" criteria).

Seam: `import rocket_physics` — the cheapest possible observation of the package. These tests
protect the "no file I/O on import" and "no re-exports" rules stated in the architecture (§7).
"""

import ast
from pathlib import Path

import rocket_physics

INIT_PATH = Path(__file__).resolve().parent.parent / "src" / "rocket_physics" / "__init__.py"


def test_version_is_exported_as_a_string() -> None:
    assert isinstance(rocket_physics.__version__, str)
    assert rocket_physics.__version__  # non-empty


def test_init_module_source_has_no_imports_and_assigns_only_version() -> None:
    # Reads the source directly rather than `vars(rocket_physics)`: once another test imports
    # `rocket_physics.errors`, Python binds `errors` onto the `rocket_physics` namespace as a
    # normal submodule-caching side effect — that is not a re-export by __init__.py, so the
    # check belongs on the file's own AST, not on live module state that other tests pollute.
    tree = ast.parse(INIT_PATH.read_text(encoding="utf-8"))
    assigned_names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise AssertionError(f"__init__.py must not import anything, found: {ast.dump(node)}")
        if isinstance(node, ast.Assign):
            for target in node.targets:
                assert isinstance(target, ast.Name)
                assigned_names.append(target.id)
    assert assigned_names == ["__version__"]
