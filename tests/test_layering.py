"""Seam 4 (layering/purity) and C5 (no shell) enforcement — written in ticket 1 (RP-001), not
later (§7, §4.2, §4.4).

RP-001 lands the subset of Seam 4 that C5 and the I6 refinement need right now: no CLI framework,
no `__main__`, no console entry point, no project-specific names in `src/`. The full AST-walk over
every L0-L4 import rule (I1-I5) is RP-002's scope and will likely promote the helpers below into
`tools/layers.py`.
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "rocket_physics"

# I6 refinement (§4.3): no module under src/ may be named after or mention a project. fx27 is the
# live example; cspace/euroc are its two campaigns (§13), named in the same architecture section.
BANNED_PROJECT_TOKENS = ("fx27", "cspace", "euroc")

BANNED_CLI_IMPORTS = ("argparse", "click", "typer")


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def _imported_module_names(source: str) -> set[str]:
    """Top-level module name of every `import x` / `from x import y` in `source`."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module.split(".")[0])
    return names


def _banned_imports_in_file(path: Path, banned: tuple[str, ...]) -> set[str]:
    return _imported_module_names(path.read_text(encoding="utf-8")) & set(banned)


def _tokens_mentioned_in_file(path: Path, tokens: tuple[str, ...]) -> set[str]:
    haystack = path.read_text(encoding="utf-8").lower()
    name_haystack = path.name.lower()
    return {
        token for token in tokens if token.lower() in haystack or token.lower() in name_haystack
    }


# -- detector unit tests (synthetic fixtures; independent of the real src/ tree) ----------------


def test_banned_import_detector_flags_a_cli_framework_import(tmp_path: Path) -> None:
    module = tmp_path / "offender.py"
    module.write_text("import argparse\n", encoding="utf-8")
    assert _banned_imports_in_file(module, BANNED_CLI_IMPORTS) == {"argparse"}


def test_banned_import_detector_flags_a_from_import(tmp_path: Path) -> None:
    module = tmp_path / "offender.py"
    module.write_text("from click import command\n", encoding="utf-8")
    assert _banned_imports_in_file(module, BANNED_CLI_IMPORTS) == {"click"}


def test_banned_import_detector_allows_a_clean_module(tmp_path: Path) -> None:
    module = tmp_path / "clean.py"
    module.write_text("import numpy as np\n\n\ndef f(x):\n    return np.sin(x)\n", encoding="utf-8")
    assert _banned_imports_in_file(module, BANNED_CLI_IMPORTS) == set()


def test_project_token_detector_flags_a_mention_in_a_comment(tmp_path: Path) -> None:
    module = tmp_path / "offender.py"
    module.write_text("# tuned for the fx27 campaign\nX = 1\n", encoding="utf-8")
    assert _tokens_mentioned_in_file(module, BANNED_PROJECT_TOKENS) == {"fx27"}


def test_project_token_detector_flags_a_mention_in_a_filename(tmp_path: Path) -> None:
    module = tmp_path / "cspace_motor.py"
    module.write_text("X = 1\n", encoding="utf-8")
    assert _tokens_mentioned_in_file(module, BANNED_PROJECT_TOKENS) == {"cspace"}


def test_project_token_detector_allows_a_clean_module(tmp_path: Path) -> None:
    module = tmp_path / "clean.py"
    module.write_text("X = 1\n", encoding="utf-8")
    assert _tokens_mentioned_in_file(module, BANNED_PROJECT_TOKENS) == set()


# -- real-tree guards (always green by construction; they fail the moment someone regresses) ----


def test_no_cli_framework_imports_under_src() -> None:
    violations = {
        str(path.relative_to(REPO_ROOT)): hit
        for path in _iter_py_files(SRC_ROOT)
        if (hit := _banned_imports_in_file(path, BANNED_CLI_IMPORTS))
    }
    assert violations == {}


def test_no_dunder_main_under_src() -> None:
    offenders = [str(p.relative_to(REPO_ROOT)) for p in SRC_ROOT.rglob("__main__.py")]
    assert offenders == []


def test_no_project_specific_names_under_src() -> None:
    violations = {
        str(path.relative_to(REPO_ROOT)): hit
        for path in _iter_py_files(SRC_ROOT)
        if (hit := _tokens_mentioned_in_file(path, BANNED_PROJECT_TOKENS))
    }
    assert violations == {}


def test_no_console_scripts_in_pyproject() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    assert "scripts" not in project
    assert "gui-scripts" not in project
    entry_points = project.get("entry-points", {})
    assert "console_scripts" not in entry_points
