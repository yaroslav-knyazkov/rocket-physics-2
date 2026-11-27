# Tickets — Stage 1: scaffold, first vertical slice, point mass → 2D → 3D

**Status: READY TO IMPLEMENT.** Gate #2 cleared 2026-11-27 — stack and architecture approved
(`dev/docs/architecture-stage1.md`, §9). Start at **RP-001**.

## Кратко (RU)

- Разбивка стадии 1 на тикеты для `developer`. Все архитектурные решения утверждены, гейтов больше
  нет — можно начинать с RP-001.
- Порядок моделей динамики — по решению пользователя: **точечная масса (RP-008) → 2D с тангажом
  (RP-011) → полные 6 степеней свободы (RP-012)**.
- Сначала инфраструктура, которая удерживает дисциплину: каркас пакета (RP-001), тест-страж слоёв и
  запрета CLI (RP-002), типы (RP-003), схема конфигов (RP-004), интегратор с двумя адаптерами
  (RP-005), протоколы и реестр моделей с тестовыми заглушками (RP-006), скелет LaTeX с проверялкой
  соответствия коду (RP-007).
- Первый вертикальный срез (RP-008) выбран так, чтобы у него было **точное аналитическое решение**:
  полёт точечной массы в вакууме. Первый же тест проверяет физику, а не вывод собственного кода.
- Валидация по fx27 (RP-009) — **один набор тестов, здесь, на настоящих числах fx27**. Не начинать,
  пока пользователь не скажет, откуда берутся эталонные числа (§12, п. 11 архитектуры): выгрузки
  OpenRocket, результаты порта v1, `rocketpy` или телеметрия реального полёта — это разные виды
  истины и разные допуски.
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

| Layout | Fields | `n_state` |
|---|---|---|
| `point` | `pos(d)`, `vel(d)`, `mass`, with `d ∈ {1,2,3}` a layout parameter | `2d + 1` |
| `planar` | `pos(2)`, `vel(2)`, `pitch`, `pitch_rate`, `mass` | 7 |
| `6dof` | `pos(3)`, `vel(3)`, `quat(4)`, `omega(3)`, `mass` | 14 |

`Trajectory` holding `t: (K,)`, `y: (N, K, n_state)`, `layout`, `aux: dict[str, ndarray]`, with named
accessors (`traj.altitude`, `traj.velocity`) over slices — **no caller ever indexes a raw column**,
which is what lets a metric written against `planar` keep working on `6dof`.
Then `EventLog`, `Provenance`, `SimulationResult`, `OptimizationResult`, each with `to_dict()`
producing JSON-safe output.
`units.py`: SI conversion helpers, documented as edge-only (I5). `constants.py`: physical constants,
each carrying an `Implements:`/`Docs:` back-reference to `docs/appendix/constants.tex` (§8.3).

Tests: `to_dict()` round-trip; accessor correctness for all three layouts; `N=1` and `N>1` shapes;
a `Trajectory` built with mismatched shapes raises rather than silently broadcasting (that last one
is the bug class this design exists to prevent).

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
- **Spec slice:** §5.4 (M1 row + why the sequence), §4.1 (layers), §6.2 (api surface sketch), §5.2 (SimulationResult), §10 (determinism, provenance)

The thinnest path through **every** layer, deliberately chosen because it has a **closed-form
answer**: constant gravity, zero drag, constant thrust, linear mass burn, point mass.

- `rhs_point.py`: **dimension-parametric** (`d ∈ {1,2,3}`) — `dv/dt = (T + D + G)/m` is identical
  vector algebra in 1, 2 or 3 spatial components, so one implementation covers vertical ascent, a
  planar point mass and a 3D point mass. No attitude, no angle of attack, no moments.
- `frames.py`, `forces.py`: force assembly from model outputs.
- `simulations/flight.py`: returns a `SimulationResult`, **pure — it returns, it never writes** (I2).
- `metrics/flight.py`: `apogee`, `apogee_time`, `rail_exit_speed` as individual pure functions
  (this is v1's 20.7 KB `flight_stats.py`, split by concern from the start).
- `api.py`: `validate`, `run_simulation`, `list_models`, `list_simulations`, `register_model` wired
  up; `list_optimizations` returns `[]` for now.

Acceptance:
- `tests/analytic/test_vacuum_ballistic.py` asserts apogee and apogee time against the closed-form
  solution to `ANALYTIC` tolerance — **the first test in the project checks physics, not the code's
  own output**;
- the same scenario with `N=100` identical members yields 100 identical trajectories (D3 sanity + I3
  determinism);
- `d=1`, `d=2` and `d=3` agree for a purely vertical scenario;
- provenance is populated and `SimulationResult.to_dict()` round-trips.

---

### [RP-011] M2 — "2D": pitch-plane rigid body
- **Module/boundaries:** `src/rocket_physics/dynamics/rhs_planar.py`, `src/rocket_physics/models/{aerodynamics,mass,actuation}/**`, `src/rocket_physics/metrics/stability.py`, `tests/unit/dynamics/test_rhs_planar.py`, `tests/analytic/test_planar_*.py`, `tests/properties/**`
- **Assignee:** developer
- **depends_on:** [RP-008]
- **parallel_safe:** false
- **Spec slice:** §5.4 (M2 row + the "2D" ambiguity note), §4.2 (Seam 3)

Attitude enters here. State `pos(2), vel(2), pitch, pitch_rate, mass` (7). Adds angle of attack,
normal force, aerodynamic moment, pitch inertia, centre of pressure vs centre of gravity, and
**static margin** — the first model in which the word "stability" means anything, which is why the
project's own description ("trajectory *and stability* simulation") forces attitude into the middle
step. Rail-constrained launch becomes expressible here too.

Real model adapters start landing in this ticket (Barrowman aero, linear-burn mass,
first-order-lag actuator), each with its `.tex` section implemented or `\simtodo`-marked per §8, and
each with the mandatory batch/scalar property test.

Acceptance: static margin and short-period frequency match analytic expressions for a simple
geometry; a planar run with zero angle of attack and zero moment reproduces the M1 point-mass result
— a free cross-model regression test, and the reason the progression is layered this way.

**Note before starting:** §5.4 flags that "2D" is read as *planar rigid body with pitch*, not *planar
point mass*. One line of confirmation via the orchestrator if anything in fx27's needs contradicts it.

---

### [RP-012] M3 — "3D": full 6-DOF rigid body
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

**Note before starting:** §5.4 flags that "3D" is read as *full 6-DOF*. If fx27 actually needs v1's
*frozen-attitude* model (3D translational, carrying a non-rotating attitude state — v1's port chose it
deliberately at a user gate), that is an **M2.5** `rhs_frozen.py`, ~1-2 days, inserted before this
ticket and disturbing nothing above or below. One line of confirmation from the user first.

---

### [RP-009] fx27 validation suite  *(single suite, in this repo — D6b)*
- **Module/boundaries:** `tests/validation/fx27/**` (including `tests/validation/fx27/data/`), `tests/tolerances.py`
- **Assignee:** developer
- **depends_on:** [RP-008]  *(can start against M1; grows with RP-011 and RP-012)*
- **parallel_safe:** false
- **NEEDS ONE ANSWER FIRST:** §12 item 11 — **which oracle supplies the reference numbers**, which
  campaign/vehicle to validate first, and which quantities count. Not a blocker for RP-001…RP-008.
- **Spec slice:** §9 D6b (approved shape + its four consequences), §4.3 (I6 refinement), §10 (tolerance policy), §12 item 11, §13 (fx27 candidate reference data)

This is the **only** validation suite that will ever exist — fx27 has none and will not get one (C8).
Binding rules from §9 D6b:

1. Real fx27 reference numbers, committed. No anonymised-fixture layer.
2. The suite imports **only `rocket_physics.api`** — it is a consumer of the public surface, exactly
   like an fx27 run file. Needing to reach past `api` means `api` has a gap; fix `api`, not the test.
   (Side benefit: this suite doubles as the honest usability test of the public interface.)
3. Runs under the `validation` marker, excluded from the default run — its failures mean "the physics
   disagrees with reality", not "the code is broken" — but it is a **release gate**, not optional.
4. Every tolerance in `tests/tolerances.py` under `VALIDATION_FX27`, and **each reference datum must
   record which oracle it came from**. The candidates differ in kind, not just in value: OpenRocket,
   v1's port and `rocketpy` are other models' opinions (percent-level agreement is a consistency
   check); flight telemetry is reality (disagreement means *our* model is wrong). A suite that mixes
   them without labelling which is which means nothing — so the label is mandatory metadata, not a
   comment.

Available material is inventoried in §13 ("fx27 candidate reference data") — do not re-probe the
fx27 folder, take it from there.

---

### [RP-010] v1 cross-check harness  *(optional; decide after RP-011)*
- **Module/boundaries:** `tests/crosscheck_v1/**`
- **Assignee:** developer
- **depends_on:** [RP-011]
- **parallel_safe:** true
- **Spec slice:** §2 (conclusion 1), §10 (tolerance policy), §13 (v1 location)

Opt-in (`-m crosscheck`) differential tests against v1 at `D:/Projects - Ongoing/rocket-physics`
(read-only; never imported by `src/`). Worth doing only once a model without a closed-form answer
exists — M1 has an exact solution and needs no oracle — so this follows RP-011, not RP-008. Raise with
the orchestrator before starting: it depends on how v1's environment is reachable from this tree.

---

## Execution order

| Wave | Tickets | Notes |
|---|---|---|
| 1 | **RP-001** | Alone. Everything depends on it. |
| 2 | **RP-003** | Types are needed by RP-004 / RP-005 / RP-006. |
| 3 | **RP-002, RP-004, RP-005, RP-006, RP-007** | Parallel. Boundaries are disjoint: RP-002 → `tests/test_layering.py` + `tools/layers.py`; RP-004 → `config/` + `tests/data/`; RP-005 → `numerics/`; RP-006 → `models/`; RP-007 → `docs/` + `tools/check_model_docs.py`. (RP-002 and RP-007 both touch `tools/`, but different files.) |
| 4 | **RP-008** (M1) | Alone — the integration point. |
| 5 | **RP-011** (M2) | After RP-008. **RP-009** may start in parallel once its oracle question is answered; **RP-010** is optional and parallel-safe. |
| 6 | **RP-012** (M3) | After RP-011. Optional **M2.5** (`rhs_frozen.py`) inserted before it only if the user confirms fx27 needs it. |

Stage 1 is complete when M1 is validated against closed form, M2 and M3 against their analytic and
cross-model checks, the §10 performance budgets are met or explicitly re-budgeted with measurements
attached, and `tests/validation/fx27/` is green against whichever oracle the user names.
