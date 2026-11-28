"""Directory skeleton per architecture-stage1.md §7 (RP-001).

"Create every directory from §7 with an `__init__.py` whose docstring names the module's layer
(L0-L5); empty packages are fine and expected." This test operationalizes that sentence as a
regression guard: later tickets fill these packages with real modules, but the layer label in each
`__init__.py` docstring must survive.
"""

from __future__ import annotations

from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "rocket_physics"

# relative dir -> expected layer tag, per the §7 tree.
EXPECTED_LAYER_DIRS: dict[str, str] = {
    "types": "L0",
    "config": "L0",
    "models": "L1",
    "models/atmosphere": "L1",
    "models/gravity": "L1",
    "models/aerodynamics": "L1",
    "models/thrust": "L1",
    "models/mass": "L1",
    "models/wind": "L1",
    "models/actuation": "L1",
    "models/sensors": "L1",
    "dynamics": "L2",
    "numerics": "L2",
    "simulations": "L3",
    "optimizations": "L3",
    "optimizations/drivers": "L3",
    "optimizations/problems": "L3",
    "metrics": "L3",
    "loaders": "L5",
    "presentation": "L5",
}


def test_every_expected_layer_directory_exists_with_a_labelled_init() -> None:
    missing: list[str] = []
    mislabelled: dict[str, str] = {}
    for rel_dir, expected_tag in EXPECTED_LAYER_DIRS.items():
        init_file = SRC_ROOT / rel_dir / "__init__.py"
        if not init_file.is_file():
            missing.append(rel_dir)
            continue
        docstring = init_file.read_text(encoding="utf-8")
        if expected_tag not in docstring:
            mislabelled[rel_dir] = docstring.splitlines()[0] if docstring else "<empty>"
    assert missing == []
    assert mislabelled == {}


def test_no_undocumented_extra_directories_under_src() -> None:
    # Guards against drift between this test's map and the actual tree: any directory under
    # src/rocket_physics/ (besides __pycache__) must be one this test knows about.
    actual_dirs = {
        str(p.relative_to(SRC_ROOT)).replace("\\", "/")
        for p in SRC_ROOT.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    }
    assert actual_dirs == set(EXPECTED_LAYER_DIRS)
