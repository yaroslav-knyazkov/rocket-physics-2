# Tickets — Stage 1: scaffold, first vertical slice, point mass → 2D → 3D

**Status: READY TO IMPLEMENT.** Gate #2 cleared 2026-11-27 — stack and architecture approved
(`dev/docs/architecture-stage1.md`, §9). Start at **RP-001**.

## Кратко (RU)

- Разбивка стадии 1 на тикеты для `developer`. Все архитектурные решения утверждены, гейтов больше
  нет — можно начинать с RP-001.
- **В работе только M1 — точечная масса, «гравитационный разворот» без подъёмной силы (RP-008).**
  Ориентация в ней есть, но кинематически производная: тяга и сопротивление строго по вектору
  скорости, угол атаки тождественно нулевой, уравнения вращения нет. Состояние —
  `pos(d), V, θ[, ψ], mass`. Формулы и ловушка с особенностью при `V = 0` — в §5.4.1 архитектуры и в
  самом тикете. Это **не** модель с «замороженной» ориентацией.
- **RP-009, RP-010, RP-011 (2D), RP-012 (3D) — отложены, начинать нельзя.** Их описания оставлены
  как заготовки. После RP-008 — доложить и ждать решения пользователя.
- Сначала инфраструктура, которая удерживает дисциплину: каркас пакета (RP-001), тест-страж слоёв и
  запрета CLI (RP-002), типы (RP-003), схема конфигов (RP-004), интегратор с двумя адаптерами
  (RP-005), протоколы и реестр моделей с тестовыми заглушками (RP-006), скелет LaTeX с проверялкой
  соответствия коду (RP-007).
- Первый вертикальный срез (RP-008) выбран так, чтобы у него было **точное аналитическое решение**:
  полёт точечной массы в вакууме. Первый же тест проверяет физику, а не вывод собственного кода.
- **Сверка с чужими моделями отложена** (слова пользователя: «dont compare against other model. just
  go with it»). Источник эталонных чисел выбирать не нужно; M1 проверяется аналитическим решением.
- Жёсткие правила на все тикеты: тесты до кода; никакого CLI/`__main__`/`print`; ядро не импортирует
  `loaders`/`presentation`/`matplotlib`; СИ внутри; слово «fx27» не встречается в `src/` нигде.

---

## Ground rules for every ticket

From the approved architecture, non-negotiable, and each one enforced by a test in RP-002:

1. **TDD.** Test first, always (`tdd` skill). A ticket whose tests were written after its code is
   rejected at review.
2. **No shell.** No CLI, no `__main__.py`, no `[project.scripts]`, no `argparse`/`click`/`typer`,
   no `print`, no logging configuration, no `examples/` runner (C5, §4.4).
3. **Purity.** No module in `types/ units.py constants.py config/ models/ dynamics/ numerics/
   simulations/ optimizations/ metrics/` may import `loaders`, `presentation`, `matplotlib`,
   `requests`, or call `open`/`np.random.*` (Seam 4, §4.3).
4. **Ensemble axis from day one.** Every model and RHS takes arrays with a leading `(N, …)` axis,
   `N=1` initially. Every model family ships a property test asserting `f(batch)[i] == f(batch[i])`
   (D3). A family without that test is an incomplete ticket.
5. **SI units inside the core**; conversion only in `config/`, `loaders/`, `presentation/` (I5).
6. **`src/` must not know the word "fx27"** (I6 as refined in §4.3). Project data lives in exactly
   one place: `tests/validation/fx27/`.
7. **No tolerance inline in a test.** All of them in `tests/tolerances.py` (§10).
8. **Named spec slice only.** `Grep -n` the section anchor in `dev/docs/architecture-stage1.md`, then
   `Read` with `offset`/`limit`. Do not read the whole spec.

Names fixed by the architecture, so nobody has to decide them mid-ticket:

| Thing | Value |
|---|---|
| Repo root | `D:/Projects - Ongoing/rocket-physics-2` (work in the assigned worktree) |
| Distribution name | `rocket-physics` |
| Import name | `rocket_physics` |
| Layout | `src/rocket_physics/…` (src-layout, actually installed, not `sys.path`) |
| Python | `requires-python = ">=3.12,<3.14"` |
| Public surface | `rocket_physics.api` — the only module a non-core caller may import |

---

### [RP-001] Repository scaffold, packaging and tooling
- **Module/boundaries:** `pyproject.toml`, `uv.lock`, `.gitignore`, `README.md`, `src/rocket_physics/__init__.py`, `src/rocket_physics/errors.py`, `src/rocket_physics/progress.py`, `tests/conftest.py`, `tests/tolerances.py`
- **Assignee:** developer
- **depends_on:** []
- **parallel_safe:** false  *(everything depends on this; run it alone, first)*
- **Spec slice:** §3 (stack table), §7 (directory structure), §13 (environment facts — take versions from here, do not re-probe)

Create the `src`-layout package `rocket_physics` with `uv` + `pyproject.toml`:
`requires-python = ">=3.12,<3.14"`; runtime deps `numpy>=2.5,<3`, `scipy>=1.18,<2`, `pydantic>=2,<3`;
extras `plots = ["matplotlib>=3.11,<4"]`, `dev = ["pytest>=9", "hypothesis", "ruff", "mypy"]`.
Configure `ruff` (lint + format), `pytest` with markers `perf`, `crosscheck`, `validation`, `docs` —
**all four excluded from the default run** via `addopts` — and `mypy` on `src/` only (advisory at this
stage, not a gate). **No `[project.scripts]`.**

Create every directory from §7 with an `__init__.py` whose docstring names the module's layer
(L0–L5); empty packages are fine and expected.

- `errors.py`: `RocketPhysicsError` base, then `ConfigError`, `ModelError`, `IntegrationError`,
  `StepFailure` (subclass of `IntegrationError`), `ConvergenceError`, `Cancelled`.
- `progress.py`: `ProgressSink` protocol (`on_step(frac: float, message: str) -> None`) and `NullSink`.
- `tests/tolerances.py`: the single home of numerical tolerances, pre-seeded with the five families
  from §10 (`ANALYTIC`, `REGRESSION`, `CROSSCHECK_V1`, `VALIDATION_FX27`, `PERF`) and a comment
  stating that no test may define a tolerance locally.
- `__init__.py` exposes `__version__` only — no re-exports, no side effects.

Done when `uv sync` succeeds, `pytest` collects without error, `ruff check` and
`ruff format --check` pass, and `python -c "import rocket_physics"` performs no file I/O.

---

### [RP-002] Layering / purity / no-shell enforcement test (Seam 4)
- **Module/boundaries:** `tests/test_layering.py`, `tools/layers.py`
- **Assignee:** developer
- **depends_on:** [RP-001]
- **parallel_safe:** true
- **Spec slice:** §4.1 (layer diagram), §4.2 (Seam 4), §4.3 (invariants table + the I6 refinement), §4.4 (no shell)

AST-walk every module under `src/rocket_physics/`. One test function per rule, each failing with a
message naming the offending file and line:

1. The layer table lives in `tools/layers.py` (module path → layer 0–5). A new top-level package with
   no entry **fails loudly** — this is what keeps the table from rotting.
2. No module in L0–L4 imports `rocket_physics.loaders`, `rocket_physics.presentation`, `matplotlib`,
   `requests`, `urllib`, `pathlib`, `os` or `sys`. Allow-list exceptions must be explicit and
   commented in `tools/layers.py`.
3. No module in L0–L4 contains `open(`, a module-level `np.random.<fn>` call, `print(`, or
   `logging.basicConfig`.
4. Import direction is downward only: a module at layer N imports nothing above N.
5. **No shell (C5):** no `__main__.py` anywhere in `src/`; no `[project.scripts]` or
   `console_scripts` in `pyproject.toml`; no `argparse`, `click` or `typer` import anywhere in the
   package.
6. **No project names in `src/` (I6):** no module path, module name, identifier or string literal
   under `src/` matches `fx27`, `cspace` or `euroc` (case-insensitive). A companion test asserts the
   only directory in the repo referencing them is `tests/validation/`.

This ticket keeps every later ticket honest, which is why it comes second and not last.

---

### [RP-003] Value types: state layouts, Trajectory, results
- **Module/boundaries:** `src/rocket_physics/types/**`, `src/rocket_physics/units.py`, `src/rocket_physics/constants.py`, `tests/unit/types/**`
- **Assignee:** developer
- **depends_on:** [RP-001]
- **parallel_safe:** true
- **Spec slice:** §5.2 (result types table), §5.3 (ensemble axis), §5.4 (the three state layouts), §4.3 (I4, I5)

`State` as a **layout descriptor** (index names → slices), with all three layouts from §5.4 defined
now even though only `point` is used by RP-008:

| Layout | Fields | `n_state` | Status |
|---|---|---|---|
| `point` | **flight-path-angle parameterisation** (§5.4.1): `d=1` → `h, V, mass`; `d=2` → `x, h, V, θ, mass`; `d=3` → `x, y, h, V, θ, ψ, mass` | 3 / 5 / 7 | **in scope** |
| `planar` | `pos(2)`, `vel(2)`, `pitch`, `pitch_rate`, `mass` | 7 | deferred — placeholder only |
| `6dof` | `pos(3)`, `vel(3)`, `quat(4)`, `omega(3)`, `mass` | 14 | deferred — placeholder only |

**Define `point` properly; the other two are placeholders** that exist only to prove the
layout-descriptor mechanism generalises. Do not invest in them and do not let them shape `point`.

`θ` gets a named accessor `traj.flight_path_angle` whose docstring states it is a **kinematic
quantity, not a rotational state** (§5.4.1). That is the one naming trap in this ticket: when a
genuine `pitch` state arrives with M2 later, the two must stay separately named — they differ exactly
by the angle of attack, which is identically zero in M1 and non-zero in M2.

`Trajectory` holding `t: (K,)`, `y: (N, K, n_state)`, `layout`, `aux: dict[str, ndarray]`, with named
accessors (`traj.altitude`, `traj.speed`, `traj.flight_path_angle`) over slices — **no caller ever
indexes a raw column**, which is what lets a metric survive a later change of layout.
Then `EventLog`, `Provenance`, `SimulationResult`, `OptimizationResult`, each with `to_dict()`
producing JSON-safe output.
`units.py`: SI conversion helpers, documented as edge-only (I5). `constants.py`: physical constants,
each carrying an `Implements:`/`Docs:` back-reference to `docs/appendix/constants.tex` (§8.3).

Tests: `to_dict()` round-trip; accessor correctness for the `point` layout at `d = 1, 2, 3`; `N=1`
and `N>1` shapes; a `Trajectory` built with mismatched shapes raises rather than silently
broadcasting (that last one is the bug class this design exists to prevent).

---

### [RP-004] Config schema (pydantic v2)
- **Module/boundaries:** `src/rocket_physics/config/**`, `tests/unit/config/**`, `tests/data/demo_rocket.toml`
- **Assignee:** developer
- **depends_on:** [RP-001, RP-003]
- **parallel_safe:** false  *(creates `tests/data/`)*
- **Spec slice:** §5.1 (schema table + rules), §4.3 (I3 seed, I5 units)

One module per aggregate exactly as §5.1 lists — **do not create a single `schema.py`**; that is the
named v1 anti-pattern (v1's own was 28.4 KB). Enforce the §5.1 rules: no callables, no numpy arrays
and no file paths in any config field; `schema_version: int` and `seed: int` on `Scenario`.
`selection.py` is names-only, resolved later against the model registry. Validation failures raise
`ConfigError` wrapping pydantic's message. Provide `Scenario.json_schema()` for the §6.2 catalogue.

`tests/data/demo_rocket.toml` is a **generic** fixture — round numbers, invented vehicle, no fx27
material (real fx27 artefacts belong under `tests/validation/fx27/data/`, RP-009).

Tests: the fixture validates; each rule violation raises `ConfigError`;
`Scenario -> dict -> Scenario` is an exact round-trip; an unknown model name in `selection.py` fails
at validation time, not at run time.

---

### [RP-005] Numerics: Integrator seam, vectorised fixed-step RK4, events
- **Module/boundaries:** `src/rocket_physics/numerics/**`, `tests/unit/numerics/**`, `tests/properties/test_integrator.py`
- **Assignee:** developer
- **depends_on:** [RP-001, RP-003]
- **parallel_safe:** true
- **Spec slice:** §4.2 (Seam 2), §9 D2 (approved: option c), §9 D3 (approved: option a), §10 (numerical robustness)

- `integrator.py`: the `Integrator` protocol and `IntegratorResult`, with §4.2's invariants written
  into the docstring (explicit deterministic step grid; RHS called an implementation-defined number
  of times per step; no state retained between calls; leading ensemble axis).
- `rk4.py`: fixed-step RK4, **vectorised over the leading `(N, …)` axis**, allocation-free in the
  inner loop (pre-allocated work arrays), step grid aligned to a control sample rate via `grid.py`.
  This is the production integrator.
- `scipy_ivp.py`: `solve_ivp` adapter — **verification only**; raises a clear error for `N > 1`.
- `events.py`: sign-change detection plus bisection refinement to a declared time tolerance; events
  record the **refined** time, not the step time.

Tests — this is the ticket where property tests earn their keep:
- convergence order: halving the step divides the error by ~16 on a linear ODE with a known solution;
- batch/scalar equivalence: `integrate(batch)[i] == integrate(batch[i])`;
- the two adapters agree within `ANALYTIC` tolerance on a smooth problem — **this is the entire
  justification for D2 option c, so it is not optional**;
- event time for an analytically known zero-crossing is correct to the stated tolerance;
- a diverging RHS raises `IntegrationError` with the failing state attached;
- an out-of-domain RHS input clamps and records a warning rather than raising (§10).

---

### [RP-006] Model protocols, registry, and the trivial test adapters
- **Module/boundaries:** `src/rocket_physics/models/protocols.py`, `src/rocket_physics/models/registry.py`, `src/rocket_physics/models/*/constant.py`, `src/rocket_physics/models/*/zero.py`, `src/rocket_physics/models/README.md`, `tests/unit/models/test_registry.py`
- **Assignee:** developer
- **depends_on:** [RP-001, RP-003]
- **parallel_safe:** true
- **Spec slice:** §4.2 (Seam 3), §5.1 (`selection.py` row), §6.2 (catalogue functions), §8.1 (docs mapping)

One `typing.Protocol` per model family (atmosphere, gravity, aerodynamics, thrust, mass, wind,
actuation, sensors), array-in/array-out, carrying the ensemble axis.
`registry.py`: `family -> {name -> factory}` with `register()`/`get()`/`list()`, populated by
**explicit imports only — no filesystem scanning** (§6.2: no module-level side effects). Each entry
carries `name`, `title`, `docs_label` and the pydantic config model for that adapter.

Implement **only the trivial test adapters** here — `constant` density, `zero` wind, `constant`
thrust, `constant` gravity. They come first, not last, because they are what makes every later
physics ticket testable in isolation: a planar or 6-DOF test can hold seven models constant and vary
one. That is the concrete mechanism by which this architecture supports TDD rather than fighting it.

`models/README.md`: the models ↔ `docs/models/*.tex` index table from §8.1.

---

### [RP-007] LaTeX skeleton + the docs↔code checker
- **Module/boundaries:** `docs/**`, `tools/check_model_docs.py`, `tests/test_model_docs.py`
- **Assignee:** developer
- **depends_on:** [RP-001]
- **parallel_safe:** true
- **Spec slice:** §8 in full (§8.1–§8.4, short)

Create the `docs/` tree from §7: `main.tex`, `preamble.tex` (the `\simtodo`/`\restodo`/`\figtodo`/
`\comptodo` macro definitions — copy them from v1's `dev/docs/latex-v2/main.tex`, read-only at
`D:/Projects - Ongoing/rocket-physics`), a `Makefile` running `latexmk` + `makeindex` for
nomenclature, and one stub `.tex` per `models/` family, each with `\label{model:<family>}` and a
`\restodo{}` placeholder. Add the `docs/numerical/`, `docs/systems/`, `docs/analysis/`,
`docs/appendix/` stubs per §7 — including `docs/systems/flight.tex` with a subsection per dynamics
model from §5.4. **Do not write physics content** — the user writes the derivations.

`tools/check_model_docs.py`: the three both-directions assertions in §8.4, exposed as a function so
`tests/test_model_docs.py` asserts on it with readable failures. Register it under the `docs` pytest
marker (excluded from the default run per RP-001) and flag back to the orchestrator that §12 item 7
— blocking vs advisory — is still the user's call; the marker makes either answer a one-line change.

---

### [RP-008] M1 — point mass: first vertical slice, end to end
- **Module/boundaries:** `src/rocket_physics/dynamics/{frames.py,forces.py,rhs_point.py}`, `src/rocket_physics/simulations/{registry.py,flight.py}`, `src/rocket_physics/api.py`, `src/rocket_physics/metrics/flight.py`, `tests/analytic/test_vacuum_ballistic.py`, `tests/unit/dynamics/**`, `tests/unit/simulations/**`, `tests/unit/metrics/**`
- **Assignee:** developer
- **depends_on:** [RP-003, RP-004, RP-005, RP-006]
- **parallel_safe:** false  *(the integration point — do not parallelise it with anything)*
- **Spec slice:** **§5.4.1 in full (M1's equations — read this one properly)**, §5.4 (table), §4.1 (layers), §6.2 (api surface sketch), §5.2 (SimulationResult), §10 (determinism, provenance)

The thinnest path through **every** layer, deliberately chosen because it has a **closed-form
answer**: constant gravity, zero drag, constant thrust, linear mass burn, point mass.

- `rhs_point.py` — **M1: the zero-lift gravity turn.** Thrust and drag act exactly along the velocity
  vector, so the angle of attack is identically zero and the vehicle's orientation *is* its velocity
  direction. Attitude is therefore present but **kinematically derived — there is no rotational
  equation and no torque anywhere in this model**:

  ```
  dV/dt = (T - D)/m - g·sin(θ)
  dθ/dt = -g·cos(θ) / V
  dx/dt =  V·cos(θ)·cos(ψ)
  dy/dt =  V·cos(θ)·sin(ψ)        # d = 3 only
  dh/dt =  V·sin(θ)
  dψ/dt =  0                      # no side force ⇒ heading constant
  dm/dt = -ṁ(t)
  ```

  **This is NOT a frozen/fixed-attitude model** — that would hold θ constant regardless of the
  velocity direction, implying α ≠ 0 and a lift force the model then ignores. Do not implement it
  that way, and say so in the module docstring so a later agent cannot "helpfully" reinterpret it.
  **Dimension-parametric** (`d ∈ {1,2,3}`): one implementation covers vertical ascent (`d=1`, θ ≡ π/2
  and the dθ/dt equation drops out), the planar gravity turn (`d=2`) and the 3D case (`d=3`, where ψ
  is constant, so 3D buys orientation of the trajectory plane rather than out-of-plane motion).

  **Mandatory:** `dθ/dt` is singular at `V = 0`, which is exactly the state at ignition and
  near-exactly a vertical apogee. Guard on `V` below a declared threshold and hold θ, consistent with
  §10's "the RHS must never raise on out-of-domain input", and **test it**. This is the one real
  numerical trap in M1; the docstring must state what happens there, not just the code.
- `frames.py`, `forces.py`: force assembly from model outputs.
- `simulations/flight.py`: returns a `SimulationResult`, **pure — it returns, it never writes** (I2).
- `metrics/flight.py`: `apogee`, `apogee_time`, `rail_exit_speed` as individual pure functions
  (this is v1's 20.7 KB `flight_stats.py`, split by concern from the start).
- `api.py`: `validate`, `run_simulation`, `list_models`, `list_simulations`, `register_model` wired
  up; `list_optimizations` returns `[]` for now.

Acceptance:
- `tests/analytic/test_vacuum_ballistic.py` asserts apogee and apogee time against the closed-form
  solution to `ANALYTIC` tolerance — **the first test in the project checks physics, not the code's
  own output**. With `T = 0`, `D = 0`, constant `g` and `θ₀ = π/2` the gravity-turn equations reduce
  to vacuum ballistics exactly, so the oracle is unambiguous.
- a second analytic case with `θ₀ < π/2` (`T = 0`, `D = 0`): the gravity turn reduces to a parabola,
  so range, apogee and the final θ all have closed forms. **This is the test that actually checks the
  dθ/dt equation** — the vertical case alone would pass with that term missing entirely.
- `V → 0` guard: a scenario reaching `V = 0` (vertical apogee, and ignition at rest) completes
  without raising, without NaN, and with θ held — see the mandatory note above.
- the same scenario with `N=100` identical members yields 100 identical trajectories (D3 sanity + I3
  determinism);
- `d=1`, `d=2` and `d=3` agree for a purely vertical scenario;
- provenance is populated and `SimulationResult.to_dict()` round-trips.

**Stop after this ticket.** M2/M3 are deferred (below); the user will ask for M2 explicitly once M1
is built and validated.

---

### [RP-011] M2 — "2D": pitch-plane rigid body  —  ⛔ **DEFERRED, DO NOT START**
- **Status:** **deferred by the user 2026-11-27.** Scope right now is M1 only. The user will ask for
  this explicitly once M1 is built and validated. **`developer` must not start this ticket**, and must
  not pre-build parts of it inside RP-008 "while we're here".
- **Module/boundaries:** `src/rocket_physics/dynamics/rhs_planar.py`, `src/rocket_physics/models/{aerodynamics,mass,actuation}/**`, `src/rocket_physics/metrics/stability.py`, `tests/unit/dynamics/test_rhs_planar.py`, `tests/analytic/test_planar_*.py`, `tests/properties/**`
- **Assignee:** developer
- **depends_on:** [RP-008]
- **parallel_safe:** false
- **Spec slice:** §5.4 (M2 row + the M2/M3 reading note), §4.2 (Seam 3)

*Forward note only — kept so the design accommodates it and so it is not re-derived later.*

**Dynamical** attitude enters here: state `pos(2), vel(2), pitch, pitch_rate, mass` (7), with its own
moment equation. Note the real increment over M1 is **not** "attitude appears" — M1 already carries a
kinematic θ (§5.4.1). It is that attitude becomes an independent state, which is what makes α ≠ 0
possible and with it normal force, aerodynamic moment, pitch inertia, CP vs CG and **static
margin** — everything the word "stability" means. Rail-constrained launch becomes expressible here too.
`pitch` and M1's `flight_path_angle` must stay separately named: they differ exactly by α.

Real model adapters start landing in this ticket (Barrowman aero, linear-burn mass,
first-order-lag actuator), each with its `.tex` section implemented or `\simtodo`-marked per §8, and
each with the mandatory batch/scalar property test.

Acceptance: static margin and short-period frequency match analytic expressions for a simple
geometry; a planar run with zero angle of attack and zero moment reproduces the M1 point-mass result
— a free cross-model regression test, and the reason the progression is layered this way.

**When it is eventually unblocked:** §5.4 records that "2D" is read as *planar rigid body with pitch*,
not *planar point mass* (M1's `d = 2` case already is a planar point mass). Confirm with the user at
that point, not now.

---

### [RP-012] M3 — "3D": full 6-DOF rigid body  —  ⛔ **DEFERRED, DO NOT START**
- **Status:** **deferred by the user 2026-11-27.** Blocked behind RP-011, which is itself deferred.
  Forward note only.
- **Module/boundaries:** `src/rocket_physics/dynamics/{rhs_6dof.py,quaternion.py}`, `src/rocket_physics/models/{wind,sensors}/**`, `src/rocket_physics/metrics/{loads.py,dispersion.py}`, `src/rocket_physics/simulations/{ensemble.py,sweep.py}`, `tests/**`
- **Assignee:** developer
- **depends_on:** [RP-011]
- **parallel_safe:** false
- **Spec slice:** §5.4 (M3 row + the frozen-attitude M2.5 note), §5.3 (ensemble axis), §10 (perf budgets)

State `pos(3), vel(3), quat(4), omega(3), mass` (14). Adds three-axis rotation via quaternion, full
inertia tensor, roll and roll damping, fin cant, 3D wind and crosswind weathercocking, lateral drift
and landing dispersion. `simulations/ensemble.py` (Monte Carlo over the `N` axis) and `sweep.py` land
here, since this is the first model where dispersion analysis is meaningful.

Acceptance: a 6-DOF run constrained to the pitch plane reproduces the M2 planar run within
`REGRESSION` tolerance; quaternion round-trip and normalisation property tests; rotation-invariance
property test (rotating the inertial frame rotates the trajectory and nothing else); the §10
performance budgets for the single flight and the 1 000-member ensemble are met, or the §10 revisit
ladder (profile → numba → Rust) is triggered **with measurements attached**.

**When it is eventually unblocked:** §5.4 records that "3D" is read as *full 6-DOF*. If fx27 turns out
to need v1's *frozen-attitude* model (3D translational, holding a non-rotating attitude state — v1's
port chose it deliberately at a user gate), that is an **M2.5** `rhs_frozen.py`, ~1-2 days, inserted
before this ticket. Note it is **a different model from M1** despite both being called "point mass"
loosely: a frozen attitude implies α ≠ 0 and hence lift, whereas M1's α ≡ 0 by construction (§5.4.1).

---

### [RP-009] fx27 validation suite  —  ⛔ **DEFERRED, LOW PRIORITY, DO NOT START**
- **Status:** **deferred by the user 2026-11-27.** Verbatim: *"dont compare against other model. just
  go with it… at some point we will compare but it shouldn't be this necessary."* **No oracle needs
  picking, and nothing about this ticket is urgent.** M1 is verified against its closed-form solution,
  which is a stronger check than agreement with another simulator. Do not raise the oracle question
  with the user; they will raise comparison when they want it.
- **Module/boundaries:** `tests/validation/fx27/**`, `tests/tolerances.py`
- **Assignee:** developer
- **depends_on:** [RP-008]
- **parallel_safe:** false
- **Spec slice:** §9 D6b, §4.3 (I6 refinement), §10 (tolerance policy), §13 (fx27 candidate reference data)

*Forward note only.* When comparison does become wanted, the shape is already settled: one suite,
here, real fx27 numbers, no anonymised layer (fx27 has no suite of its own and will not get one, C8);
imports only `rocket_physics.api`; `validation` marker; tolerances in `tests/tolerances.py` under
`VALIDATION_FX27`; and each reference datum labelled with **which oracle** it came from, since
OpenRocket / v1's port / `rocketpy` are other models' opinions while flight telemetry is reality, and
mixing the two kinds unlabelled makes a suite meaningless. Candidate material is inventoried in §13
— do not re-probe the fx27 folder.

---

### [RP-010] v1 cross-check harness  —  ⛔ **DEFERRED**
- **Status:** **deferred 2026-11-27** by the same user decision as RP-009 — no comparison against
  other models for now. Do not start.
- **Module/boundaries:** `tests/crosscheck_v1/**`
- **Assignee:** developer
- **depends_on:** [RP-011]
- **parallel_safe:** true
- **Spec slice:** §2 (conclusion 1), §10 (tolerance policy), §13 (v1 location)

*Forward note only.* Opt-in (`-m crosscheck`) differential tests against v1 at
`D:/Projects - Ongoing/rocket-physics` (read-only; never imported by `src/`). Pointless before a model
without a closed-form answer exists — M1 has an exact solution and needs no oracle at all.

---

## Execution order

| Wave | Tickets | Notes |
|---|---|---|
| 1 | **RP-001** | Alone. Everything depends on it. |
| 2 | **RP-003** | Types are needed by RP-004 / RP-005 / RP-006. |
| 3 | **RP-002, RP-004, RP-005, RP-006, RP-007** | Parallel. Boundaries are disjoint: RP-002 → `tests/test_layering.py` + `tools/layers.py`; RP-004 → `config/` + `tests/data/`; RP-005 → `numerics/`; RP-006 → `models/`; RP-007 → `docs/` + `tools/check_model_docs.py`. (RP-002 and RP-007 both touch `tools/`, but different files.) |
| 4 | **RP-008** (M1) | Alone — the integration point. **This is the last ticket in scope.** |
| — | ⛔ RP-009, RP-010, RP-011, RP-012 | **All deferred.** Do not start any of them. Report back after RP-008 and wait for the user. |

**Scope ends at RP-008.** Seven tickets: RP-001 → RP-003 → {RP-002, RP-004, RP-005, RP-006, RP-007}
→ RP-008.

Done when: `uv sync` / `ruff` / `pytest` are green; the layering + no-shell + no-"fx27"-in-`src/`
tests pass; the vectorised RK4 and the `solve_ivp` verification adapter agree on a smooth problem;
and M1 reproduces the closed-form vacuum solution **in both the vertical and the inclined
(`θ₀ < π/2`) case**, with the `V → 0` guard tested. Then stop and report — the user decides what
comes next.
