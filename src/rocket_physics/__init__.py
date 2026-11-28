"""rocket_physics: a pure, importable library for rocket trajectory and stability simulation,
control implementation and optimization.

This module exposes only `__version__`. No re-exports, no side effects — importing it must never
touch the filesystem, network, clock or stdout (I1, §4.3). The public surface lives in
`rocket_physics.api`.
"""

__version__ = "0.1.0"
