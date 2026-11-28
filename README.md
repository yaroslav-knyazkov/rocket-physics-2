# rocket-physics

A pure, importable Python library for rocket trajectory and stability simulation, control
implementation and optimization. It has no command-line interface and no application shell: it is
a dependency, consumed by run files that live in other repositories.

## Install

```bash
uv add rocket-physics
# or, during development, from a checkout:
uv pip install -e .
```

## Usage

The public surface (`rocket_physics.api`) is not implemented yet at this stage of the build — see
`dev/docs/task-stage1.md` ticket RP-008. Once it lands, a usage example will be added here.

## Documentation

The physics derivations (equations of motion, model assumptions, numerical methods) live in
`docs/` as a LaTeX document — see `docs/main.tex`. Architecture and ticket history for this
build live in `dev/docs/`.
