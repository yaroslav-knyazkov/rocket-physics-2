# Architecture — Stage 1: core stack, seams and repository structure

Status: **APPROVED 2026-11-27 — Gate #2 (stack + architecture) cleared.** All of D1–D6 are settled;
two user overrides are folded in (D6b, and the dynamics rollout order) — see §9.
Stage: 1 (greenfield). Author: `architect`, 2026-11-27.
Inputs: `dev/docs/idea-notes.md`; read-only inspection of v1 (`D:/Projects - Ongoing/rocket-physics`)
and of the driving project folder (`D:/Projects - Ongoing/fx27`).
Implementation plan: `dev/docs/task-stage1.md`. Start at ticket **RP-001**.

## Кратко (RU)

- Документ фиксирует стек, границы модулей (seams) и структуру каталогов ядра `rocket-physics-2`.
  **Все решения утверждены пользователем 2026-11-27** — это не предложение, а норма. Код не пишется:
  скелет делает `developer` по тикетам из `task-stage1.md`, начиная с RP-001.
- **Стек утверждён: Python 3.12 + NumPy 2.5 + SciPy 1.18, зависимости через `uv`, тесты
  `pytest` + `hypothesis`, конфиги на `pydantic` v2.** Главный довод не производительность, а то, что
  v1 написан на Python и служит численным эталоном, а fx27 (ведущий проект) — тоже Python. Смена
  языка оторвала бы v2 от обоих. Альтернативы (Python + ядро на Rust; Julia) разобраны и отложены,
  для Rust оставлен явный шов (Seam 2).
- **Ядро абсолютно чистое:** ни файловой системы, ни сети, ни печати, ни глобального генератора
  случайных чисел. Всё «грязное» — в двух необязательных пакетах-сайдкарах `loaders/` (читалки
  файлов) и `presentation/` (отчёт и графики); ядро их никогда не импортирует, и правило проверяется
  автотестом направления импортов с первого дня. Это архитектурный ответ на главную ошибку v1
  («сначала построили, потом тестировали»).
- **CLI и любой «запускающий» слой в этом репозитории отсутствуют** (решение пользователя от
  2026-11-27): ни `__main__`, ни console-entry-point, ни `examples/`-раннера. Репозиторий — только
  импортируемый пакет. Все файлы запуска, разбор аргументов, пути и сохранение картинок живут в
  `fx27`.
- **Таксономия Models / Simulations / Optimizations** — три соседних пакета, у каждого реестр
  (`registry`), который перечисляет доступные элементы вместе с их JSON-схемой конфигурации и ссылкой
  на раздел LaTeX. Этот реестр — то, что позже будет читать GUI; специальной работы под GUI сейчас
  не делается.
- **Порядок усложнения модели динамики задан пользователем: точечная масса → 2D → 3D** (§5.4).
  В переводе на код: `rhs_point.py` (поступательное движение без ориентации, одна и та же функция для
  1/2/3 пространственных измерений) → `rhs_planar.py` (плоская задача с тангажом — первая модель, где
  вообще появляется устойчивость) → `rhs_6dof.py` (полные 6 степеней свободы с кватернионом).
  Неоднозначность слова «2D» помечена в §5.4 — взято наиболее естественное чтение, не заблокировано.
- **LaTeX ведёт за собой код:** `docs/models/<модель>.tex` соответствует
  `src/rocket_physics/models/<модель>/` один к одному; каждая реализованная формула имеет метку
  `\label{eq:<модель>:<имя>}`, а функция в коде — строку `Implements: eq:<модель>:<имя>`. Скрипт
  сверяет обе стороны, расхождение падает как тест.
- **Связь с `fx27` закрыта:** этот репозиторий — ядро-пакет, `fx27` — потребитель, в нём лежат файлы
  запуска, которые импортируют пакет и вызывают Models / Simulations / Optimizations. Подключение —
  editable-установка по пути (`uv pip install -e …`) в venv проекта fx27; переход на колесо с
  зафиксированной версией — только когда число из ядра впервые попадёт в отчёт или LaTeX.
- **Валидация по fx27 — ровно один набор тестов, и он здесь:** `tests/validation/fx27/` с настоящими
  эталонными числами fx27, без слоя «обезличенных фикстур» (пользователь отклонил мою схему из двух
  наборов; своих тестов у fx27 нет и не будет). Это единственное исключение из правила «ничего
  проектного в репозитории»: проектные **данные** — только в `tests/validation/fx27/`, проектный
  **код** — нигде и никогда (I6 в §4.3).
- **HTTP/RPC и GUI не делаются и даже не «закладываются»** — по решению пользователя «API» здесь
  означает ровно импортируемый пакет. Будущий GUI — такой же внешний потребитель, как `fx27`.
- **Открыт один нетупиковый вопрос** (§12, п. 11): из какого источника брать эталонные числа для
  `tests/validation/fx27/` — выгрузки OpenRocket (в fx27 лежат 4 файла `.ork`), результаты порта v1,
  или телеметрия реального полёта. RP-001…RP-008 этого не ждут; нужно к RP-009.

## Table of contents

- [1. Context and constraints](#1-context-and-constraints)
- [2. What v1 actually looks like (evidence)](#2-what-v1-actually-looks-like-evidence)
- [3. Chosen stack](#3-chosen-stack)
- [4. Components, seams and relations](#4-components-seams-and-relations)
- [5. Data model and configuration schema](#5-data-model-and-configuration-schema)
- [6. Public interface (the "API")](#6-public-interface-the-api)
- [7. Directory structure](#7-directory-structure)
- [8. LaTeX <-> code contract](#8-latex---code-contract)
- [9. Settled decisions (approved 2026-11-27)](#9-settled-decisions-approved-2026-11-27)
- [10. Non-functional decisions](#10-non-functional-decisions)
- [11. Rejected options](#11-rejected-options)
- [12. Open questions — status](#12-open-questions--status)
- [13. Environment facts (cached, do not re-probe)](#13-environment-facts-cached-do-not-re-probe)

## 1. Context and constraints

Fixed by the user, not re-litigated here:

| # | Constraint | Architectural consequence |
|---|---|---|
| C1 | v2 is a package/library — "API" means exactly *an importable package*, nothing more exotic | No `projects/` directory in this repo. Project-specific code lives in the consumer. |
| C2 | TDD from day one; v1 failed by build-then-test | The core must be callable with no setup: pure functions, in-memory inputs, no filesystem, no global state. |
| C3 | Build around one concrete project (`fx27`) first, generalize after | Registries and seams are designed now, but only the fx27-needed adapters are implemented. No speculative model zoo. |
| C4 | End state: GUI over Models / Simulations / Optimizations | The taxonomy is a structural fact of the repo from day one; it is cheap now and expensive to retrofit. The GUI itself is a *consumer*, outside this repo. |
| C5 | **No CLI, no app shell, no entry points in this repo** (user, 2026-11-27) | There is no shell layer to design. Run files, argument parsing, printing and "go" buttons all live in `fx27`. See §4.4. |
| C6 | LaTeX is written first | The repo must have a landing spot for `.tex` that mechanically binds to code. |
| C7 | `fx27` holds the **run files** — project scripts that import this package and call Models/Simulations/Optimizations (user, 2026-11-27) | `fx27` is a consumer, not a sibling effort and not a sub-repo. No project *code* lands here. |
| C8 | **`fx27` has no test suite of its own and will not get one** (user, 2026-11-27) | The only validation suite in existence is `tests/validation/fx27/` in *this* repo, using fx27's real reference numbers. See D6b and the I6 refinement in §4.3. |
| C9 | **Dynamics models arrive in the order: point mass → 2D → 3D** (user, 2026-11-27) | Fixes the ticket order and the state-layout design. Translated to concrete models in §5.4. |

Nothing in this section is open any more. The one remaining non-blocking question is the *source* of
the fx27 reference numbers (§12, item 11) — needed for RP-009, not for RP-001…RP-008. Persistence
(a database) is not needed and is not assumed.

**No database is assumed.** Run outputs are files in a run directory (§10). If a results catalogue is
ever wanted (the GUI browsing past runs), that is a later, separate decision; nothing in this stage
depends on it.

## 2. What v1 actually looks like (evidence)

Measured, not recalled — read-only inspection of `D:/Projects - Ongoing/rocket-physics`:

- Stack: **Python 3.12, `numpy==2.5.4`, `scipy>=1.18,<2`, `matplotlib>=3.11,<4`, `pytest>=8`.**
  Packaging was deliberately retired there: `requirements.txt` is the single dependency declaration
  and the package is *not* installed into the interpreter (see the comment block in v1's
  `pyproject.toml`). v2 reverses this — see §3.
- Physics core: `apps/sim/engine/` — 30 modules, **8 719 lines**. Largest:
  `integrate.py` 1 142, `aero.py` 908, `soundings.py` 585, `control.py` 579, `dynamics.py` 475,
  `report.py` 452, `params.py` 439, `wind.py` 425.
- Application layers: `apps/{sim,analysis,control,optimization,input}` plus `apps/_shared`
  (`flight_stats.py` 20.7 KB, `artifacts.py`). `apps/sim/schema.py` is **28.4 KB in one file** — the
  clearest shallow-module smell in v1: a large interface (every config field a caller must know)
  over a thin implementation (validation + defaults).
- **`projects/fx27/` lives inside the v1 repo** — exactly the structure C1 forbids. It has its own
  `solvers/point/{flight,ideal_rewrite,ideal_open_airbrake,comparison,estimate,metrics,plots,validity,runcli}.py`,
  its own `_docs/latex/`, `data/`, `runs/`.
- Tests: **59 `test_*.py` files** under `tests/`. Notably `test_layering.py` and
  `test_packaging_boundary.py` already exist — v1 had learned to assert its own layering. v2 keeps
  that idea and promotes it to a day-one invariant (§4, Seam 4).
- LaTeX: 34 `.tex` files. `dev/docs/latex-v2/` is the live draft and already carries the taxonomy v2
  should adopt: `sections/models/{aerodynamics,atmosphere,gravity,mass,noise,noninertial,thrust,wind}.tex`,
  `sections/numerical/{states,sampled}.tex`, `sections/systems/flight.tex`, `sections/analysis/analysis.tex`,
  `sections/appendix/{conventions,constants,model-inventory}.tex`, plus `assumptions/`, `backlog/`, `intro/`.
  It also defines useful marker macros: `\simtodo{}` (in the paper, not yet in the simulator),
  `\restodo{}` (needs research), `\figtodo{}`, `\comptodo{}`. **v2 adopts these macros and gives
  `\simtodo` a mechanical meaning** (§8).
- `fx27` folder: `dossier-de-definition/`, `open-rocket/`, `simulation-1/`, `simulation-3/`
  (empty today). **`fx27` is not a git repository** — no `.git`. `simulation-1/rocket_physics_port/`
  is a copy of v1's `projects/fx27` package (its README says: a port of the `rocketpy`-based
  `fx27/simulation` onto v1's `apps/`, two campaigns `cspace`/`euroc`, 7 entry points under `runs/`).
  This is decisive input for D6 (§9) — a submodule story is weak when the consumer is not a repo.

Two conclusions carried into the design:

1. **The physics content of v1 is a numerical oracle for v2.** 8.7 kLOC of engine plus 59 test files
   in the *same language* means v2 can assert "same answer as v1 within tolerance" with a few lines
   of glue. This is the single strongest argument in the stack decision (§3) and it is a
   project-specific argument, not a general preference for Python.
2. **v1's defects are structural, not linguistic.** Monolithic config schema, project code inside the
   library, I/O interleaved with physics (`report.py`, `plotting.py`, `datafiles.py`, `soundings.py`
   sitting inside `engine/`). Changing language would not have fixed any of them; changing seams does.

## 3. Chosen stack

**Approved 2026-11-27 (decision D1 in §9). This table is the stack — not a proposal.**

| Concern | Choice | Why this one |
|---|---|---|
| Language / runtime | **Python 3.12** (`requires-python = ">=3.12,<3.14"`) | 3.12.10 is what is installed; v1 and fx27 both run on it. Pinning the floor at 3.12 keeps the three code bases interchangeable during the fx27-driven phase. |
| Arrays | **NumPy 2.5** (`numpy>=2.5,<3`) | Same major as v1 (`2.5.4`), so v1 outputs are byte-comparable where they should be. |
| Scientific primitives | **SciPy 1.18** (`scipy>=1.18,<2`) | Needed for `optimize` (root finding, `minimize`, `least_squares`, `differential_evolution`), `interpolate` (thrust curves, aero tables, sounding profiles) and `integrate.solve_ivp` as the *verification* integrator (§9 D2). |
| Packaging / env | **`uv` + `pyproject.toml`, src-layout, real installable distribution** | Reverses v1's decision to retire packaging. C1 ("v2 is a library") only means something if the thing is actually installable: fx27 consumes it as `rocket-physics` (editable during development), not via `sys.path` games. `uv` 0.12 is already installed. |
| Tests | **`pytest` 9 + `hypothesis`** | pytest 9.1.1 already installed. `hypothesis` is the part v1 lacked: physics has natural properties (energy/momentum bookkeeping, frame-transform round-trips, monotonicity of drag in speed, invariance under rotation of the inertial frame) and property tests catch the class of bug that golden files miss. |
| Config / validation | **`pydantic` v2** (decision D4) | See §5. One dependency buys: validation at the edge (so the core can assume valid input), JSON Schema emission, and exact (de)serialisation for golden-file tests and reproducible run records. |
| Plots / reports | **`matplotlib`, optional extra** (`pip install rocket-physics[plots]`) | Plotting is I/O. It must not be importable from the core, and it must not be a hard dependency of a headless consumer. v1 had `plotting.py` inside `engine/`; v2 does not. |
| Lint / format | **`ruff`** (lint + format, single tool) | Zero-config enough not to become a project of its own; its `flake8-tidy-imports` banned-API rules are how Seam 4 (§4) is enforced cheaply. |
| Typing | **`mypy`** on `src/` only, strict-ish; no runtime type coercion in the core | The core's interface *is* its contract; types are the cheapest part of documenting it. Not a blocker in CI at stage 1 (advisory), to avoid typing overhead fighting TDD. |
| Numerical escape hatch | **none installed now**; `numba` reserved behind Seam 2 | See D1 option B and §10. The seam exists from day one; the dependency does not. |

Explicitly **not** in the stack at stage 1: any web framework, any database/ORM, any task queue, any
plotting-in-core, any GUI toolkit, `rocketpy` (v1's fx27 predecessor — it is prior art and a possible
cross-check target, not a dependency).

### Rationale for Python over the alternatives

The honest technical ranking on *numerics alone* would put Julia first. The decision is not made on
numerics alone, and here is the concrete reason:

1. **The oracle argument (§2, conclusion 1).** v2's whole purpose is to be correct where v1 was
   unvalidated. The cheapest validation available is differential testing against v1's 8.7 kLOC
   engine. In Python that is `import` + `assert_allclose`. In Julia it is a cross-language harness
   (subprocess + serialisation + two environments) that someone has to build and maintain — pure
   overhead that produces no physics.
2. **The driving-project argument (C3).** fx27's existing material (`simulation-1/rocket_physics_port`,
   the `rocketpy`-based `simulation`) is Python. Choosing another language makes "build around fx27
   first" mean "rewrite fx27 first", which inverts the user's stated plan.
3. **The TDD-loop argument (C2).** The failure mode being designed against is *untested code*, so
   the metric that matters is how cheap a red-green cycle is: `pytest -k <name>` on a cold Python
   interpreter is ~1 s. Julia's compile-on-first-call latency and a Rust rebuild both add seconds to
   tens of seconds per cycle; over thousands of cycles that is the dominant cost, and the project that
   dies of friction is the project that stops writing tests.
4. **The agent-team argument.** `developer`/`qa`/`security` in this kit are configured around pytest,
   ruff and uv. A Julia or Rust core means re-adapting the kit (`/adapt-kit`, profile commands, QA
   gates) before any physics gets written.

Performance — the one real objection to Python — is addressed architecturally rather than by language
choice, and the design keeps the language escape hatch open:

- The integrator is **vectorised over the ensemble axis** (D3): state array shape `(N, n_state)`, so a
  1 000-member Monte Carlo costs ~1 `numpy` call per step instead of 1 000 Python loops. This is the
  single biggest lever and it is free if decided now, expensive later (it changes every model's
  signature).
- The right-hand side is a **pure array-in/array-out function with no I/O and no allocation of Python
  objects**, which makes it a drop-in target for `numba.njit` or a Rust/PyO3 kernel *behind the same
  seam*, with no caller changes (Seam 2, §4).
- A **named performance budget** (§10) turns "is it fast enough" into a test rather than an opinion,
  with an explicit trigger for revisiting D1 option B.

## 4. Components, seams and relations

Vocabulary is from the `codebase-design` skill: *module* = anything with an interface and an
implementation; *interface* = everything a caller must know (types, invariants, error modes,
performance characteristics); *seam* = where an interface lives and behaviour can be swapped without
editing in place; *deep* = much behaviour behind a small interface.

### 4.1 Layer diagram

```
   outside   ┌──────────────────────────────────────────────────────────┐
   this      │  fx27 run files   ·   (much later) a GUI                 │  consumers
   repo      └───────────────────────────┬──────────────────────────────┘
                                         │  import rocket_physics
         ┌───────────────────────────────┼──────────────────────────────┐
  L5     │  loaders/   optional, impure: .eng/.rse, soundings, CSV ──►  │  file -> config
  side-  │  presentation/  optional: report text, matplotlib figures    │  result -> artifact
  cars   │  (never imported by L0–L4; consumers may skip them entirely) │
         └───────────────────────────────┼──────────────────────────────┘
                                         │  Seam 1: rocket_physics.api
         ┌───────────────────────────────▼──────────────────────────────┐
  L4     │  api.py          the ONLY public surface. Pure. Thin.        │
         └───────────────────────────┬──────────────────────────────────┘
         ┌───────────────────────────▼──────────────────────────────────┐
  L3     │  simulations/    (flight, ensemble, sweep)   + registry      │
         │  optimizations/  (Problem, drivers)          + registry      │
         └──────────┬─────────────────────────────┬─────────────────────┘
                    │                             │  Seam 2: numerics.Integrator
         ┌──────────▼──────────────┐   ┌───────────▼─────────────────────┐
  L2     │  dynamics/              │   │  numerics/                      │
         │  frames, quaternion,    │   │  integrator protocol, rk4       │
         │  rhs_point -> rhs_planar│   │  (vectorised), scipy adapter,   │
         │  -> rhs_6dof   (§5.4)   │   │  events, step grid, sampling    │
         │  (assembles models      │   │  — model-agnostic               │
         │   into one RHS)         │   │                                 │
         └──────────┬──────────────┘   └─────────────────────────────────┘
                    │  Seam 3: model protocols
         ┌──────────▼──────────────────────────────────────────────────┐
  L1     │  models/   atmosphere, gravity, aerodynamics, thrust, mass, │
         │            wind, actuation, sensors, noise  + registry      │
         │            PURE. One .tex section each (§8).                │
         └──────────┬──────────────────────────────────────────────────┘
         ┌──────────▼──────────────────────────────────────────────────┐
  L0     │  types/ (State, Trajectory, Result…)  units/  constants/    │
         │  config/ (pydantic schema — pure validation, no file access)│
         └─────────────────────────────────────────────────────────────┘
```

**Import direction is strictly downward.** `L0 ≤ L1 ≤ L2 ≤ L3 ≤ L4`, and L5 may import anything below
it while **nothing in L0–L4 may import L5**. This is Seam 4 and it is enforced by a test, not by
discipline (§4.3).

L5 is *not* a shell and *not* an application: `loaders/` and `presentation/` are optional sidecar
subpackages the consumer may call, skip or replace. Whether they belong in this package at all is
decision D5 (§9).

### 4.2 The four seams

**Seam 1 — `rocket_physics.api`: the public surface.**
*Interface:* a handful of functions, each taking a validated config object (or a plain dict/JSON) and
returning an in-memory result object. No file paths, no printing, no progress bars, no globals.
*Callers above it:* fx27's run files (now) and, much later, a GUI — **both outside this repo.** Two
independent caller families already shape the signature (a script that wants objects; a GUI that wants
JSON plus an enumerable catalogue), so the seam is real, not hypothetical.
*Depth:* very deep. `run_simulation(config)` hides model wiring, integrator choice, event handling,
sampling and result assembly behind one call.
*Deletion test:* delete it and every caller re-derives the wiring order of eight models — it earns its keep.

**Seam 2 — `numerics.Integrator`: the integration kernel.**
*Interface:* `integrate(rhs, y0, t_grid, events, …) -> IntegratorResult`, where `rhs` is a pure
`(t, y) -> dy` over arrays of shape `(N, n_state)` and `y0` has the same leading ensemble axis.
Invariants a caller must know: the step grid is explicit and deterministic; the RHS is called an
implementation-defined number of times per step; no state is retained between calls.
*Adapters from day one:* `FixedStepRK4` (production — vectorised, deterministic, control-friendly) and
`ScipySolveIvp` (verification — adaptive, dense output, event root-finding). Two adapters exist
immediately, so the seam is justified on day one rather than speculative. *Later adapters:* `numba`
kernel, Rust/PyO3 kernel — this is the escape hatch that makes D1 option B reachable without rework.

**Seam 3 — model protocols.**
*Interface:* one `typing.Protocol` per model family, e.g.
`AtmosphereModel.state(altitude) -> AtmosphereState`, `AeroModel.coefficients(flow, controls) -> AeroCoefficients`,
`ThrustModel.thrust(t, ambient_pressure) -> float|array`.
*Adapters:* real ones (ISA, radiosonde-table, fx27 aero table, measured thrust curve) *and test ones*
(constant density, zero wind, constant thrust). The test adapters are the reason this seam pays for
itself immediately: a 6-DOF test can hold seven models constant and vary one. That is the concrete
mechanism by which this structure "does not fight TDD".

**Seam 4 — purity / layering.**
*Interface:* an invariant rather than a signature — **no module in L0–L4 performs I/O.** Data files
(`.eng`/`.rse` thrust curves, radiosonde soundings, aero tables) are turned into in-memory arrays by
`loaders/` and handed to the core inside a validated config.
*Enforcement:* `tests/test_layering.py` walks the AST of every module in `src/rocket_physics/` and
fails on a forbidden import (`loaders`, `presentation`, `matplotlib`, `open`, `pathlib`-as-reader,
`requests`, module-level `numpy.random` singletons) from L0–L4; plus `ruff`'s banned-API rules as a
fast local signal. v1 already had `test_layering.py` and `test_packaging_boundary.py`; v2 writes them
in the first ticket rather than retrofitting them.

### 4.4 There is no shell in this repo (C5)

Stated explicitly so no later agent re-invents one: this package has **no `__main__`, no console
entry point in `pyproject.toml`, no argument parsing, no `print`, no logging configuration and no
`examples/` runner.** The separation that TDD needs is *pure core vs optional impure sidecars*
(Seam 4), which is achieved without any application layer. Everything shell-shaped — argument
parsing, run directories, "which scenario do I run today", figures for a report — is a run file in
`fx27`.

Two consequences the `developer` must respect:

- Anything that wants to be observable from outside is a **returned value** or a **`ProgressSink`
  callback** (§6.2), never a print. A library that prints cannot be embedded.
- Reusable *mechanism* may live here (an `.eng` parser, a trajectory plot function); reusable
  *policy* may not (where files go, what a run is called, which models a given rocket uses).

### 4.3 Invariants the whole design rests on

| ID | Invariant | Why it matters | How it is checked |
|---|---|---|---|
| I1 | The core never touches the filesystem, network, clock or stdout | Makes every core test a pure unit test: no fixtures, no temp dirs, no mocks | `tests/test_layering.py` |
| I2 | Simulations and optimizations **return** results; they never write them | Side-effect-free interface = trivially testable; persistence is the shell's job | layering test + review |
| I3 | All randomness flows through an explicitly passed `numpy.random.Generator`, seeded from config | Monte Carlo must be bit-reproducible, or regression tests are noise | layering test bans global `np.random` calls; a seed-equality test |
| I4 | Every model is stateless between calls; integrator state lives only in the integrator | Lets the integrator re-evaluate the RHS freely (adaptive methods, ensembles) | property test: calling a model twice with equal inputs gives equal outputs |
| I5 | Units are SI everywhere inside the core; conversion happens only at the config and presentation edges | v1-class bug source; one rule removes the whole class | naming convention + `units/` helpers used only in `config/`, `loaders/`, `presentation/` |
| I6 | No project-specific **code** in `src/` — ever. Project-specific **data** is allowed in exactly one place: `tests/validation/fx27/` | C1/C7/C8; this is the v1 mistake being designed out, narrowed to permit the single validation suite the user approved (D6b) | layering test: no module under `src/` may be named after or mention a project (`fx27`, `cspace`, `euroc`); a second test asserts no file outside `tests/validation/` references them |

**On the I6 refinement.** v1's defect was project *code* inside the library (`projects/fx27/solvers/…`),
not project *numbers* in a test. A validation test is a consumer of the public surface that happens to
live in this repo: it imports `rocket_physics.api` like any run file would, and `src/` stays unaware
it exists. The line to hold is therefore sharp and testable — **`src/` must not know the word
"fx27"** — rather than a vague "keep the project out".

## 5. Data model and configuration schema

There is **no database** (see §1). The "data model" here is (a) the declarative input schema and
(b) the in-memory result types. Both are versioned value types, not tables.

### 5.1 Input schema — `config/`

Pydantic v2 models, one file per aggregate, deliberately *not* one 28 KB `schema.py` (v1's smell):

| Module | Aggregate | Key fields (indicative, to be fixed by fx27's actual needs) |
|---|---|---|
| `config/vehicle.py` | `Vehicle` | `dry_mass`, `reference_area`, `length`, `cg_dry`, `inertia_dry`, `geometry` (nose/body/fins), `aero: AeroSpec` |
| `config/motor.py` | `Motor` | `propellant_mass`, `burn_time`, `thrust_curve: ThrustCurveSpec` (samples resolved in memory), `nozzle_exit_area`, `cg_offset`, `inertia_contribution` |
| `config/site.py` | `Site` | `latitude`, `longitude`, `elevation`, `rail_length`, `rail_azimuth`, `rail_elevation` |
| `config/environment.py` | `Environment` | `atmosphere: AtmosphereSpec` (ISA \| table), `wind: WindSpec` (zero \| power-law \| profile table), `gravity: GravitySpec` (constant \| inverse-square \| WGS84) |
| `config/control.py` | `ControlSpec` | `law` (open-loop \| PD \| …), `sample_rate_hz`, gains, actuator limits, `sensor: SensorSpec` |
| `config/scenario.py` | `Scenario` | `vehicle`, `motor`, `site`, `environment`, `control`, `dynamics` (3DOF \| frozen-attitude \| 6DOF), `integration: IntegrationSpec`, `seed` |
| `config/dispersion.py` | `Dispersion` | per-field distributions for Monte Carlo: `{"vehicle.dry_mass": {"normal": [m, σ]}}` |
| `config/registry.py` | model selection | `{"atmosphere": "isa", "aero": "fx27-table", …}` → resolved against the model registry |

Rules:

- **Every spec is JSON/TOML-round-trippable.** No callables, no numpy arrays and no file paths inside
  a config. A "custom thrust curve" is `{"kind": "samples", "t": [...], "F": [...]}`, resolved from a
  `.eng` file by `loaders/` *before* the config is built — not a `Callable[[float], float]` field.
  This is the price of serialisability and it is paid deliberately: it is what makes golden-file
  tests, reproducible run records and (later) GUI forms all fall out for free.
- Where expressivity is genuinely needed (a bespoke control law), the escape hatch is a **named
  registry entry**, not an inline lambda: the consumer registers `"fx27-pd"` and the config names it.
  Consumer-supplied adapters are how fx27 extends the core without code landing in `src/`.
- Schemas carry a `schema_version: int`. A result file records the schema version that produced it,
  so a stale golden file fails loudly instead of silently comparing apples to pears.

### 5.2 Result types — `types/`

| Type | Contents | Notes |
|---|---|---|
| `State` | state-vector layout: index names + slices, one layout per dynamics model (`point`, `planar`, `6dof` — §5.4) | A *layout descriptor*, not a per-step object. Trajectories are arrays; a per-step Python object is the classic numerical-Python performance mistake. |
| `Trajectory` | `t: (K,)`, `y: (N, K, n_state)`, `layout: State`, `aux: dict[str, ndarray]` | `N` = ensemble size (1 for a single run). Named accessors (`traj.altitude`) over slices, so callers never index raw columns. |
| `EventLog` | detected events with time, index, kind (`rail_exit`, `burnout`, `apogee`, `max_q`, `ground_impact`, `airbrake_open`) | Produced by the integrator's event machinery, not re-derived downstream. |
| `FlightMetrics` | apogee, apogee time, max Mach, max dynamic pressure, rail-exit speed, stability margin history, landing point | v1's `flight_stats.py` (20.7 KB) split by concern; every metric a pure function `Trajectory -> value`, individually testable. |
| `SimulationResult` | `trajectory`, `events`, `metrics`, `config_echo`, `provenance` | `provenance` = library version, schema version, git describe, seed. Required for any claim that a number is reproducible. |
| `OptimizationResult` | `x_opt`, `objective`, `constraints`, `iterations`, `history`, `inner: list[SimulationResult] \| None` | `history` makes convergence inspectable (and testable) rather than a black box. |

### 5.3 Why `Trajectory` is array-shaped with an ensemble axis

Choosing `(N, K, n_state)` now rather than `(K, n_state)` is cheap (`N=1` everywhere initially) and
unlocks the whole performance story in §3. Retrofitting the leading axis later means touching every
model, the integrator, every metric and every test — that is why it was decision D3 and not an
implementation detail. **Approved: vectorise from day one.**

### 5.4 Dynamics models and their rollout order (C9)

The user set the progression verbatim: *"first we start with point mass, then 2D, then 3D."*
Translated to concrete models, state layouts and ticket order:

| # | Model | Module | State layout (per member) | What it adds | First ticket |
|---|---|---|---|---|---|
| M1 | **Point mass** — translational only, no attitude | `dynamics/rhs_point.py` | `pos(d), vel(d), mass` where `d ∈ {1,2,3}` spatial components | Thrust, gravity, drag along the velocity vector, mass depletion. No rotation, no angle of attack, no moments. | RP-008 |
| M2 | **2D — pitch-plane rigid body** | `dynamics/rhs_planar.py` | `pos(2), vel(2), pitch, pitch_rate, mass` → 7 | Attitude. Angle of attack, normal force, aerodynamic moment, pitch inertia, centre of pressure vs centre of gravity, **static margin** — the first model in which the word "stability" means anything. Rail-constrained launch becomes expressible. | RP-011 |
| M3 | **3D — full 6-DOF rigid body** | `dynamics/rhs_6dof.py` | `pos(3), vel(3), quat(4), omega(3), mass` → 14 | Three-axis rotation via quaternion, full inertia tensor, roll and roll damping, fin cant, 3D wind and crosswind weathercocking, lateral drift and landing dispersion. | RP-012 |

Why this is the right increment sequence and not an arbitrary one:

- **M1 is dimension-parametric, which dissolves most of the ambiguity in the user's wording.** A
  point-mass right-hand side is `dv/dt = (T + D + G)/m` — vector algebra that is identical in 1, 2 or
  3 spatial components. One implementation, with `d` a layout parameter, covers "vertical ascent",
  "planar point mass" and "3D point mass". So *no work is thrown away* and the step to M2 is a real
  step rather than a re-parametrisation.
- **M2 therefore means "attitude arrives", not merely "two spatial dimensions."** That is the reading
  taken — see the ambiguity note below.
- **M3 is a strict superset of M2** in physics, but *not* in state layout (quaternion vs scalar pitch),
  which is precisely why `State` is a layout descriptor and metrics are written against named
  accessors rather than raw column indices (§5.2). A metric written for M2 keeps working on M3.
- Each step is independently validatable: M1 against closed-form vacuum ballistics, M2 against
  static-margin and short-period-frequency analytics, M3 against M2 (a 6-DOF run constrained to the
  pitch plane must reproduce the planar run) — that last one is a free, strong regression test and it
  only exists because the progression is layered this way.

**Ambiguity, flagged rather than silently resolved (per the coordinator's instruction).** "2D" has two
plausible readings:

- **(a) planar point mass** — 2 spatial dimensions, still no attitude;
- **(b) planar rigid body** — attitude in the plane (pitch), angle of attack, moments. **Taken.**

Reading (b) is taken for two reasons: under (a) the "2D" step would be a no-op, because M1's
dimension parameter already covers a planar point mass; and the project's own description is
"trajectory **and stability** simulation", which is unreachable without attitude — so attitude has to
enter at some step, and the middle step is the only natural place. If the user meant (a), the fix is
cheap and local: M1 already covers it, and M2 simply becomes the 3-DOF-planar-with-pitch model under
a different label.

Similarly flagged: **"3D" is read as full 6-DOF.** v1's own fx27 port deliberately chose an
intermediate *frozen-attitude* rigid body ("Option C" at a user gate, per
`fx27/simulation-1/rocket_physics_port/README.md`) — a 3D translational model carrying a non-rotating
attitude state. If fx27 needs that specific model rather than full 6-DOF, it is an **M2.5**
(`dynamics/rhs_frozen.py`) between M2 and M3, roughly 1-2 days, and it does not disturb anything
above or below. Worth one sentence of confirmation from the user before RP-012 starts; it does not
block RP-001…RP-011.

## 6. Public interface (the "API")

### 6.1 What "API" means here — settled by the user (2026-11-27)

"Built as an API" means **an installable Python package with one deliberate public surface**, imported
by fx27's run files. Nothing more exotic: no HTTP, no RPC, no CLI, no server. The package *is* the API.

### 6.2 `rocket_physics.api` — surface sketch

```python
# Catalogue — what a consumer (an fx27 run file today, a GUI later) enumerates. Each entry:
# name, title, docs label (§8), JSON Schema of its config, kind of result returned.
def list_models(family: str | None = None) -> list[ModelInfo]: ...
def list_simulations() -> list[SimulationInfo]: ...
def list_optimizations() -> list[OptimizationInfo]: ...

# Execution — pure: config in, result out. No paths, no printing.
def validate(config: Mapping | Scenario) -> Scenario: ...                  # raises ConfigError
def run_simulation(name: str, config: Mapping | Scenario,
                   *, progress: ProgressSink | None = None) -> SimulationResult: ...
def run_optimization(name: str, config: Mapping | OptimizationConfig,
                     *, progress: ProgressSink | None = None) -> OptimizationResult: ...

# Extension — how a consumer (fx27) plugs in its own model without code in src/
def register_model(family: str, name: str, factory: Callable[..., Any],
                   *, docs_label: str | None = None) -> None: ...
```

Notes on the interface, since "interface" includes invariants and error modes:

- `progress` is an optional **sink protocol** (`on_step(frac, message)`), not a print and not a
  logger. A long optimization must be observable, and a core that prints is not a library. An fx27
  run file passes a `tqdm`-backed sink; tests pass `None`. This is the *only* way the core talks
  outward besides its return value.
- Errors are a small declared hierarchy — `ConfigError`, `ModelError`, `IntegrationError`
  (sub-case: `StepFailure`), `ConvergenceError` — never a bare `ValueError`/`AssertionError` from deep
  inside. A caller must be able to tell "bad input" from "the solver failed".
- Cancellation: a `progress` sink may raise `Cancelled`; the integrator checks between steps. Cheap
  now, and it is the one thing a caller cannot bolt on from outside later.
- **No module-level side effects anywhere in the package**: `import rocket_physics` must not read
  files, configure logging, set numpy error states or build registries by scanning the filesystem.
  Registries are populated by explicit imports. This is what keeps import time ~tens of ms and test
  collection honest.

### 6.3 What is NOT in this package

No CLI, no `__main__`, no console entry point (C5). No HTTP/RPC server, no job queue, no database, no
GUI. Those are consumers or later stages and they live **outside this repo**.

The only thing done *now* to keep a future consumer cheap is already paid for by decisions taken for
other reasons: Seam 1 is the single public import path, configs are JSON-serialisable (§5.1), results
declare `to_dict()`, and the catalogue functions emit JSON Schema. No placeholder module, no reserved
directory, no abstraction added "for the GUI".

## 7. Directory structure

```
rocket-physics-2/
├── pyproject.toml              # single source of truth: deps, extras, ruff, pytest, mypy
├── uv.lock
├── README.md                   # what it is, install, 10-line usage, link to docs/
├── CLAUDE.md                   # agent kit (exists)
│
├── src/
│   └── rocket_physics/
│       ├── __init__.py         # __version__ only — no re-exports (keeps import cheap & explicit)
│       ├── api.py              # ── SEAM 1 ── the only public surface (§6)
│       ├── errors.py           # ConfigError, ModelError, IntegrationError, ConvergenceError, Cancelled
│       ├── progress.py         # ProgressSink protocol + NullSink
│       │
│       ├── types/              # L0  value types
│       │   ├── state.py        #     state-vector layouts (3dof / frozen-attitude / 6dof)
│       │   ├── trajectory.py   #     Trajectory, EventLog
│       │   └── results.py      #     SimulationResult, OptimizationResult, Provenance
│       ├── units.py            # L0  SI constants, conversion helpers (edge use only, I5)
│       ├── constants.py        # L0  physical constants  <-> docs/appendix/constants.tex
│       │
│       ├── config/             # L0  declarative input schema (pydantic v2), pure validation
│       │   ├── vehicle.py  motor.py  site.py  environment.py
│       │   ├── control.py  scenario.py  dispersion.py
│       │   ├── selection.py    #     which model adapter per family
│       │   └── schema_version.py
│       │
│       ├── models/             # L1  ── SEAM 3 ── PURE physics, one package per family
│       │   ├── registry.py     #     family -> {name -> factory}; also serves api.list_models()
│       │   ├── protocols.py    #     AtmosphereModel, AeroModel, ThrustModel, ... (the seam)
│       │   ├── atmosphere/     #     isa.py, table.py, constant.py (test adapter)
│       │   ├── gravity/        #     constant.py, inverse_square.py, wgs84.py
│       │   ├── aerodynamics/   #     barrowman.py, table.py, constant.py
│       │   ├── thrust/         #     curve.py, constant.py, pressure_corrected.py
│       │   ├── mass/           #     linear_burn.py, from_curve.py
│       │   ├── wind/           #     zero.py, power_law.py, profile.py
│       │   ├── actuation/      #     airbrake.py, first_order_lag.py, ideal.py
│       │   ├── sensors/        #     ideal.py, noisy.py
│       │   ├── noise.py        #     dispersion sampling helpers (uses injected Generator, I3)
│       │   └── README.md       #     the models <-> docs/models/*.tex index table (§8)
│       │
│       ├── dynamics/           # L2  equations of motion: models -> one RHS   (rollout: §5.4)
│       │   ├── frames.py       #     ENU / body / rail frame definitions and transforms
│       │   ├── quaternion.py   #     (needed only from M3)
│       │   ├── forces.py       #     force & moment assembly from model outputs
│       │   ├── rhs_point.py    #  M1 point mass, dimension-parametric (d = 1|2|3), no attitude
│       │   ├── rhs_planar.py   #  M2 "2D": pitch-plane rigid body — attitude, moments, margin
│       │   └── rhs_6dof.py     #  M3 "3D": full 6-DOF rigid body (quaternion, inertia tensor)
│       │                       #     (optional M2.5 rhs_frozen.py only if fx27 needs it — §5.4)
│       │
│       ├── numerics/           # L2  ── SEAM 2 ── integration, model-agnostic
│       │   ├── integrator.py   #     Integrator protocol + IntegratorResult (the seam)
│       │   ├── rk4.py          #     fixed-step, ensemble-vectorised  (default adapter)
│       │   ├── scipy_ivp.py    #     solve_ivp adapter               (verification adapter)
│       │   ├── events.py       #     zero-crossing detection + bisection refinement
│       │   ├── grid.py         #     step grid / control-sample-rate alignment
│       │   └── sampling.py     #     output decimation, dense-output interpolation
│       │
│       ├── simulations/        # L3  "SIMULATIONS" taxonomy
│       │   ├── registry.py
│       │   ├── flight.py       #     one nominal trajectory
│       │   ├── ensemble.py     #     Monte Carlo / dispersion (uses the N axis)
│       │   └── sweep.py        #     deterministic parameter sweep
│       │
│       ├── optimizations/      # L3  "OPTIMIZATIONS" taxonomy
│       │   ├── registry.py
│       │   ├── problem.py      #     Problem protocol: decision vars, objective, constraints
│       │   ├── drivers/        #     scipy_minimize.py, bisection.py, grid.py, de.py
│       │   └── problems/       #     apogee_targeting.py, airbrake_sizing.py, motor_selection.py
│       │
│       ├── metrics/            # L3  pure Trajectory -> number functions (v1's flight_stats, split)
│       │   ├── flight.py  stability.py  loads.py  dispersion.py
│       │
│       ├── loaders/            # L5  optional sidecar — the ONLY impure readers (scope: D5)
│       │   ├── motorfile.py    #     .eng / .rse -> in-memory thrust samples
│       │   ├── soundings.py    #     radiosonde / sounding files -> wind & atmosphere profiles
│       │   ├── tables.py       #     aero / Cd tables (CSV) -> arrays
│       │   └── configfile.py   #     TOML/JSON text -> dict -> config.validate()
│       │                       #     NOTE: readers return VALUES; they never pick paths or
│       │                       #     walk directories — the caller supplies bytes or a path.
│       │
│       └── presentation/       # L5  optional sidecar — result -> human form (scope: D5)
│           ├── report.py       #     SimulationResult -> markdown/text (returns a string)
│           └── plots.py        #     -> matplotlib Figure objects, never savefig/show
│                               #     extra: pip install rocket-physics[plots]
│
│  (NO cli/, NO __main__.py, NO console_scripts, NO examples/ runner — C5, §4.4.
│   Run files, path policy, run directories and figure saving all live in fx27.)
│
├── tests/
│   ├── conftest.py
│   ├── test_layering.py        # SEAM 4 + C5 enforcement — written in ticket 1, not later
│   ├── data/                   # tiny generic fixtures (demo_rocket.toml, a 12-point .eng)
│   ├── unit/                   # mirrors src/ 1:1; pure, fast, no files, no fixtures
│   ├── analytic/               # closed-form oracles: vacuum ballistic, const-thrust,
│   │                           #   exponential atmosphere terminal velocity, Keplerian checks
│   ├── properties/             # hypothesis: frame round-trips, rotation invariance,
│   │                           #   monotonicity, conservation, step-size convergence order
│   ├── regression/             # committed golden trajectories + tolerance policy
│   ├── tolerances.py           # THE single home of every numerical tolerance
│   ├── crosscheck_v1/          # differential tests vs rocket-physics v1 (opt-in marker)
│   ├── validation/fx27/        # THE validation suite (D6b) — real fx27 reference numbers.
│   │                           #   The only place in the repo that may name a project.
│   │                           #   data/ holds its reference artefacts; it imports only
│   │                           #   rocket_physics.api, exactly as an fx27 run file does.
│   └── perf/                   # budget tests, marker 'perf', excluded by default
│
├── docs/                       # ── THE LaTeX PRODUCT DOC (physics derivations) ──
│   ├── main.tex                # see §8
│   ├── preamble.tex            # \simtodo / \restodo / \figtodo / \comptodo macros (from v1)
│   ├── models/                 # one .tex per models/<family>  (1:1, §8)
│   ├── numerical/              # states.tex, integration.tex, sampled.tex
│   ├── systems/                # flight.tex (full EOM assembly), control.tex
│   ├── analysis/               # analysis.tex, metrics.tex
│   ├── appendix/               # conventions.tex, constants.tex, model-inventory.tex
│   ├── assumptions/  backlog/  intro/
│   └── Makefile                # latexmk + makeindex for nomenclature
│
├── tools/
│   ├── check_model_docs.py     # LaTeX <-> code label checker (§8), runs in CI as a test
│   └── bench.py                # perf budget harness
│
└── dev/                        # agent kit artifacts — unchanged, separate from docs/
    └── docs/  (architecture-*.md, task-*.md, adr/, ...)
```

Deliberate choices worth naming:

- **`src/` layout** (not a flat package): the installed package is what tests import, so a missing
  `__init__.py` or a wrong `pyproject` entry fails locally instead of in the consumer. Directly
  relevant to C1 — v1's "not installed into the interpreter" is the failure this prevents.
- **`docs/` (LaTeX product doc) is separate from `dev/docs/` (agent kit).** The physics paper is a
  deliverable of the product; `dev/docs/` is process. Mixing them means the paper inherits the kit's
  archival churn.
- **No `projects/` directory and no `examples/` runner, ever** (I6, C5). Usage examples live as
  doctest-able snippets in `README.md` and in `docs/`; generic test fixtures live in `tests/data/`.
  Anything runnable belongs to fx27.
- **`loaders/` and `presentation/` are named by role, not by mechanism** (`io` would invite anything
  impure to pile in, and it shadows the stdlib `io` module). They are sidecars, not a layer the core
  depends on: the whole package works with them deleted.
- **`metrics/` is its own package**, not methods on `Trajectory`: each metric becomes an independently
  testable pure function, which is how v1's 20.7 KB `flight_stats.py` is avoided.
- `models/`, `simulations/`, `optimizations/` are **siblings with identical shape** (`registry.py` +
  implementations). That symmetry is what makes the future GUI's three top-level tabs a rendering
  detail rather than an architecture change (C4).

## 8. LaTeX <-> code contract

This is the landing spot for the user's "write the LaTeX first" step, and it is mechanical, not a
convention nobody checks.

### 8.1 Naming is 1:1

| LaTeX | Code | Tests |
|---|---|---|
| `docs/models/atmosphere.tex` | `src/rocket_physics/models/atmosphere/` | `tests/unit/models/test_atmosphere.py` |
| `docs/models/aerodynamics.tex` | `src/rocket_physics/models/aerodynamics/` | `tests/unit/models/test_aerodynamics.py` |
| `docs/numerical/integration.tex` | `src/rocket_physics/numerics/` | `tests/unit/numerics/`, `tests/properties/test_order.py` |
| `docs/systems/flight.tex` | `src/rocket_physics/dynamics/rhs_*.py` | `tests/analytic/`, `tests/unit/dynamics/` |
| `docs/analysis/metrics.tex` | `src/rocket_physics/metrics/` | `tests/unit/metrics/` |

The taxonomy mirrors v1's `dev/docs/latex-v2/sections/` (measured in §2), so the user's existing draft
transplants without renaming.

### 8.2 Label convention

- Each section file opens with `\label{model:<family>}` (or `sec:<area>`).
- **Every equation that is meant to exist in code carries `\label{eq:<family>:<name>}`** — e.g.
  `eq:atmosphere:isa-density`, `eq:aerodynamics:normal-force-coefficient`,
  `eq:thrust:pressure-correction`.
- An equation that is derived but deliberately *not* implemented is marked `\simtodo{...}` (v1's
  macro, reused). This is the toggle that makes the checker usable while the paper runs ahead of code.

### 8.3 Code back-reference

Each implementing function's docstring carries a machine-readable line:

```python
def isa_density(altitude_m: np.ndarray) -> np.ndarray:
    """ISA density below the tropopause.

    Implements: eq:atmosphere:isa-density
    Docs: docs/models/atmosphere.tex
    """
```

### 8.4 The checker — `tools/check_model_docs.py`, run as a test

Three assertions, both directions:

1. Every `Implements:` label in `src/` resolves to a real `\label{}` in `docs/`. *Failure = code cites
   physics that was never written down.*
2. Every `eq:*` label in `docs/` **not** marked `\simtodo` has at least one `Implements:` reference.
   *Failure = the paper claims something the simulator does not do — the exact drift v1 accumulated.*
3. Every directory under `models/` has a matching `docs/models/*.tex`, and vice versa.

Result: the LaTeX-first workflow has a hard landing spot. Writing `docs/models/wind.tex` with live
equations makes the suite red until `models/wind/` implements or `\simtodo`-marks them — i.e. **the
paper generates the backlog**, which is exactly the inversion of v1's habit.

Scope note: the checker is label-level, not semantic. It cannot verify that the code computes the
equation — that is what `tests/analytic/` and `tests/properties/` are for.

## 9. Settled decisions (approved 2026-11-27)

**All seven decisions below are settled.** The comparison tables are kept deliberately: they are the
record of *why*, and the "rejected" column is what stops a later round from re-opening a closed
question. Each decision now opens with its approved outcome.

Summary for the impatient:

| ID | Decision | Outcome |
|---|---|---|
| D1 | Language / runtime | **A** — Python 3.12 + NumPy + SciPy |
| D2 | Integration strategy | **c** — own vectorised fixed-step RK4 (production) + `solve_ivp` (verification) behind one `Integrator` interface |
| D3 | Ensemble axis | **a** — vectorise from day one, `(N, …)` signatures, `N=1` initially, batch/scalar equivalence property test per family |
| D4 | Config schema | **a** — pydantic v2 + TOML/JSON, `schema_version` |
| D5 | Readers / plotting | **a** — `loaders/` + `presentation/` as optional sidecars here, return-values-only |
| D6a | fx27 dependency | **a** — editable path install in fx27's venv; pinned wheel only once a core number is first quoted |
| D6b | fx27 validation tests | **USER OVERRIDE** — single suite, in this repo, real fx27 numbers. No anonymised-fixture layer. |
| D7 | Dynamics rollout order | **USER-SPECIFIED** — point mass → 2D → 3D (§5.4) |

### D1 — Language and runtime for the numerical core  —  **APPROVED: option A**

*Purpose:* the substrate everything else is built on; changing it later means a rewrite.

| Option | Pros | Cons | Cost impact (dev time) |
|---|---|---|---|
| **A. Python 3.12 + NumPy + SciPy** (recommended) | Same language as v1 → its 8.7 kLOC engine and 59 test files become a numerical oracle with `assert_allclose`; same language as fx27's existing material, so "build around fx27 first" needs no rewrite; fastest red-green cycle (~1 s cold); `hypothesis` for property tests; agent kit (pytest/ruff/uv) works unchanged; mature readers for `.eng`/`.rse`/soundings | Slowest raw inner loop of the three; needs discipline (vectorised RHS, no per-step Python objects) or Monte Carlo gets painful; GIL means process-level parallelism only | **Baseline.** 0 setup, 0 learning. Perf discipline costs ~1-2 days of integrator design (already specified here as D3). |
| **B. Python surface + Rust kernel** (PyO3 / maturin) | 30-100× on the RHS + integrator loop; memory-safe; keeps the Python public surface, so the consumer story is identical to A; genuinely the right answer *if* the inner loop becomes the bottleneck | Rust toolchain is **not installed** on this machine; every physics change touches two languages, which doubles the TDD loop and breaks the 1:1 LaTeX↔module mapping (§8); Rust rebuild adds seconds per cycle; wheel-building becomes a chore for the consumer; the `developer`/`qa` agents need re-adapting | **+1-2 weeks** before the first physics equation is validated, then a permanent ~1.3-2× tax on every model change. |
| **C. Julia** (DifferentialEquations.jl, Optimization.jl, ForwardDiff) | Best-in-class ODE suite (stiff solvers, callbacks/events, sensitivity analysis) and automatic differentiation for gradient-based trajectory optimization, all first-party; one language, no two-language split; 10-50× over naive Python | **Not installed**; v1 becomes a cross-language oracle (subprocess + serialisation harness to build and maintain — pure overhead, zero physics); fx27's existing material would need porting, inverting the user's plan; compile-on-first-call latency hurts the TDD loop; the whole agent kit (pytest/ruff/uv gates, `/adapt-kit` profile) must be re-pointed; smaller hiring/help pool | **+2-4 weeks** (install, learn, build the v1 cross-check harness, re-adapt the kit) before the first validated equation. |

**APPROVED: A**, with Seam 2 (§4.2) written on day one so that B is reachable later as a *kernel swap
behind an unchanged interface*, not a rewrite. Explicit revisit trigger in §10. Honest note for the
record: on numerics alone option C (Julia) ranks first; it lost on the oracle, driving-project and
TDD-loop arguments, not on merit.

### D2 — Integration strategy  —  **APPROVED: option c**

*Purpose:* how trajectories are advanced in time; it dictates how discrete-time control, event
detection and Monte Carlo all behave.

| Option | Pros | Cons | Cost impact |
|---|---|---|---|
| **a. `scipy.integrate.solve_ivp` only** | Adaptive step, stiff solvers, dense output and event root-finding all free and battle-tested; least code to own | One trajectory per call → no ensemble vectorisation; a discrete-time controller at a fixed rate is a *discontinuity* that makes adaptive steppers reject steps and crawl; step grid is not reproducible across SciPy versions, so golden files are fragile | Lowest now, highest later: control + ensembles both fight it. |
| **b. Own fixed-step integrator (RK4, optional embedded RK45)** | Step grid aligns exactly with the controller sample rate — the correct model for flight software; bit-reproducible; vectorisable over the ensemble axis; trivially unit-testable (convergence order is a property test) | You own correctness; you own event detection (zero-crossing + bisection refinement); no stiff-system safety net | ~3-5 days, mostly tests. |
| **c. Both, behind one `Integrator` seam** (recommended) | `b` is the production adapter; `a` is the *verification* adapter — `tests/` assert the two agree on smooth problems, which is how you earn trust in your own integrator; second adapter also proves the seam is real | One more interface to keep honest; slight risk of the seam leaking adaptive-only features (dense output) | ~+1 day over `b`. |

**APPROVED: c.** Production runs use the fixed-step vectorised RK4; `solve_ivp` exists only to
cross-check it. This also makes "is my integrator right?" a test instead of a worry.

### D3 — Ensemble axis in model signatures  —  **APPROVED: option a**

*Purpose:* whether every model and the RHS accept arrays with a leading ensemble dimension.

| Option | Pros | Cons | Cost impact |
|---|---|---|---|
| **a. Vectorise from day one** (`(N, …)`, N=1 initially — recommended) | A 1 000-run Monte Carlo costs ~1 NumPy call per step instead of 1 000 Python loops — the whole answer to D1's performance objection; dispersion analysis becomes a first-class simulation rather than a script | Every model signature and test must think in arrays; broadcasting bugs are a real new class of defect (mitigated by property tests asserting `f(batch)[i] == f(batch[i])`) | ~+2-3 days up front, spread across models. |
| **b. Scalar/single-run now, vectorise when needed** | Simplest possible first models; easiest to read against the LaTeX | Retrofitting the leading axis later touches **every** model, the RHS, the integrator, every metric and every test — in practice it is a rewrite, and it will be needed (dispersion analysis is a stated goal of the taxonomy) | Cheaper now, ~2-3 weeks later. |
| **c. Scalar core + `multiprocessing` for ensembles** | No signature change; uses all cores; trivially correct | Process startup and pickling per run; ~8-16× ceiling instead of ~100×; `numpy.random.Generator` seeding across processes is a reproducibility trap (I3) | ~+2 days, lower ceiling, permanent reproducibility risk. |

**APPROVED: a**, with one **mandatory** property test per model family asserting batch/scalar
equivalence — `f(batch)[i] == f(batch[i])`. A model family without that test is an incomplete ticket.
(`c` remains available *on top of* `a` for embarrassingly parallel sweeps.)

### D4 — Configuration / input schema  —  **APPROVED: option a**

*Purpose:* how a consumer describes a rocket, a motor, a site, a scenario.

| Option | Pros | Cons | Cost impact |
|---|---|---|---|
| **a. `pydantic` v2 models + TOML/JSON** (recommended) | Validation with good error messages at the edge, so the core can assume valid input and skip defensive checks; JSON Schema for free (future GUI forms, future HTTP); exact round-trip → golden-file tests and reproducible run records fall out; versionable (`schema_version`) | One real dependency; forbids callables/arrays in configs (deliberate, §5.1) — "custom thrust curve as a lambda" must become a registry name or resolved samples; pydantic v2 validation has non-trivial import cost | ~2-3 days to model the fx27 aggregates. |
| **b. `dataclasses` only, v1-style Python config modules** | Zero dependencies; full Python expressivity (lambdas, numpy arrays, computed fields) | Not serialisable → no golden files, no reproducible run record, no GUI forms, no schema versioning; v1's own 28.4 KB `schema.py` is what this grows into | Cheapest now; it is the exact v1 trap. |
| **c. `dataclasses` + hand-written `from_dict`/`to_dict`** | No dependency, full control, serialisable | The converters *are* pydantic, written worse and untested; validation error messages become a project of their own | ~4-6 days and permanent maintenance. |

**APPROVED: a** — pydantic v2 + TOML/JSON, `schema_version` on `Scenario`.

### D5 — Do file readers, report rendering and plotting belong in this package?  —  **APPROVED: option a**

*Purpose:* C5 removed the shell; this asks how far "everything else" still lives here.
(This fork was created by the user's no-CLI clarification — previously this slot asked about HTTP,
which the user settled: no HTTP, ever, in this repo.)

| Option | Pros | Cons | Cost impact |
|---|---|---|---|
| **a. Keep `loaders/` + `presentation/` as optional sidecars here** (recommended) | An `.eng`/`.rse` parser and a radiosonde reader are reusable *mechanism*, not project policy — every future consumer needs them, and writing them once with tests is strictly better than fx27 owning fragile parsers; they are import-isolated and the core works with them deleted; `[plots]` stays an optional extra so a headless consumer is unaffected | Slightly blurs "pure package": there is impure code in the repo, even if quarantined; needs the layering test to stay honest | Baseline. |
| **b. Core only — fx27 owns all readers and plotting** | Maximum purity: the whole repo is provably pure, no optional extras, no matplotlib anywhere | Every future consumer re-implements an `.eng` parser; parsing bugs land in untested run files, which is precisely the v1 failure mode moved to a new address; fx27 gains ~800 lines it should not own | ~-2 days here, +1 week in fx27 and recurring. |
| **c. Split: readers here, presentation in fx27** | Readers are mechanism (keep), figures are taste (export); drops the matplotlib dependency entirely | Trajectory plots get re-written per consumer; comparison figures (the `\comptodo{}` macro in the LaTeX) want a canonical renderer near the physics | ~-1 day here, recurring cost in fx27. |

**APPROVED: a**, with the hard rule that these sidecars return **values** (strings, arrays,
`Figure` objects) and never choose paths, create directories or call `savefig`/`show`.

### D6 — `fx27` dependency mechanics + where validation tests live  —  **APPROVED (D6b overridden)**

*Purpose:* the user settled the *concept* (this repo = core package; `fx27` = run files consuming it);
this decision settled the plumbing.
Measured fact: **`fx27` is not a git repository** (no `.git` in `D:/Projects - Ongoing/fx27`); it
contains `dossier-de-definition/`, `open-rocket/` (4 `.ork` files), `simulation-1/` (holds
`rocket_physics_port/`, a copy of v1's `projects/fx27`, with real motor-curve CSVs and `cspace`/
`euroc` campaign configs) and an empty `simulation-3/`.

**D6a — how fx27 resolves the dependency:**

| Option | Pros | Cons | Cost impact |
|---|---|---|---|
| **a. Editable path install** — `uv pip install -e "D:/Projects - Ongoing/rocket-physics-2"` in fx27's venv (recommended for the current phase) | Tightest loop: edit the core, rerun an fx27 run file, see the number change — exactly what "build around one real project" needs; no publish step; no version skew to reason about | Not reproducible for anyone else; fx27 silently breaks when the core changes; no pinned version in a run record | 0 setup. |
| **b. Built wheel + pinned version** — core builds `rocket-physics==0.x.y`, fx27 pins it | Reproducible: a run record names an exact core version; the core's API breakages surface as deliberate upgrades | Every core change needs build+reinstall before fx27 sees it — kills the tight loop in exactly the phase that needs it | ~1-2 h setup, ~1 min per iteration. |
| **c. `uv` workspace** — one lockfile spanning both trees | Tight loop *and* a lockfile; `uv sync` sets both up | Requires fx27 to have a `pyproject.toml` and effectively couples the two trees into one project, which is a mild step back toward v1's coupling | ~2-3 h setup. |

**APPROVED: a now, b at the first milestone** — `uv pip install -e "D:/Projects - Ongoing/rocket-physics-2"`
in fx27's venv during development. Revisit a pinned wheel only once a number from the core is first
quoted in a report or in the LaTeX: from that moment it must be reproducible, so `provenance` (§5.2)
records the core version and fx27 pins it.

**D6b — where fx27 validation tests live:**

| Option | Pros | Cons | Cost impact |
|---|---|---|---|
| **a. Inside this repo: `tests/validation/fx27/` with committed reference numbers** ← **CHOSEN** | The core's own suite catches regressions against the driving project — which is the whole point of C3; fast, no cross-repo setup | Puts fx27-derived *data* in the general-purpose repo — a mild version of v1's sin (data, not code) | ~1 day. |
| **b. In fx27 only, running against the installed core** | Perfectly clean: zero project material here | The core can go green while silently breaking fx27; nobody runs fx27's suite during core development; C3 ("build around fx27 first") loses its teeth | ~1 day, recurring risk. |
| **c. Both: small anonymised characterisation fixtures here + the full project suite in fx27** *(was my recommendation — rejected)* | Core CI catches regressions via generic-looking goldens; fx27 keeps real geometry, soundings, flight data | Two suites to keep in step; needs a rule for what may be copied here — and it presumes fx27 *has* a suite, which it does not (C8) | ~1.5 days. |

**APPROVED: a — USER OVERRIDE of my recommendation (c).** The settled shape:

- **Exactly one validation suite exists, and it is `tests/validation/fx27/` in this repo**, using
  fx27's **real reference numbers directly**.
- **No anonymised-fixture duplication layer.** My option (c) is dropped.
- Rationale given by the user: **fx27 has no test suite of its own and will not get one** (C8). With
  no second suite to defer to, the duplication layer would buy nothing and cost a permanent
  keep-two-sets-in-step tax. My (c) silently assumed fx27 would be tested; it will not be.
- fx27 material is therefore **not** treated as confidential for this repo's git history.

Consequences now binding on implementation:

1. `tests/validation/fx27/` is the single exception to "nothing project-specific here" — and it is a
   **data and test** exception, never a code one. §4.3's I6 refinement states the testable line:
   **`src/` must not know the word "fx27".**
2. The suite imports **only `rocket_physics.api`** — it is a consumer of the public surface, exactly
   like an fx27 run file. If a validation test needs to reach past `api`, that is a gap in the public
   surface and the fix goes into `api`, not into the test. (Free benefit: this suite is now also the
   honest usability test of the public interface.)
3. It runs under the `validation` pytest marker, excluded from the default run — its failures mean
   "the physics disagrees with reality", not "the code is broken", and it is slower. Excluded by
   default, but a **release gate**, not optional.
4. `tests/data/demo_rocket.toml` stays a *generic* fixture for config/unit tests; real fx27 artefacts
   live under `tests/validation/fx27/data/`. Two jobs, two homes, no overlap.

**Still needed before RP-009 (not blocking RP-001…RP-008):** *which oracle* supplies the reference
numbers. Candidates found in `D:/Projects - Ongoing/fx27`: the 4 OpenRocket files in `open-rocket/`
(`fx27_cspace_01_03.ork`, `fx27_cspace_02_01.ork`, `fx27_cspace_03_01.ork`, `fx27_euroc_01_03.ork`);
outputs of v1's port (`simulation-1/rocket_physics_port/runs/`, 7 entry points over the `cspace` and
`euroc` campaigns, with real motor CSVs under `data/motors/`); the `rocketpy`-based original
`fx27/simulation`; or real flight telemetry, if any exists. These are *different kinds of truth* —
an OpenRocket number is another model's opinion, flight telemetry is reality — and the tolerance
policy differs by an order of magnitude between them. See §12 item 11.

### D7 — Dynamics-model rollout order  —  **USER-SPECIFIED: point mass → 2D → 3D**

*Purpose:* the order in which the equations of motion grow, which fixes both the ticket sequence and
the state-layout design.

Not a fork I offered — the user supplied their own progression verbatim ("first we start with point
mass, then 2D, then 3D"), which is a different cut from the three models I had listed (3DOF point
mass / frozen-attitude rigid body / full 6DOF). The translation into concrete modules, state layouts,
the justification for the sequence, and the two flagged ambiguities ("2D" = planar rigid body with
attitude, not planar point mass; "3D" = full 6-DOF, with v1's frozen-attitude model available as an
optional M2.5) are in **§5.4**. Ticket order follows it: RP-008 (M1) → RP-011 (M2) → RP-012 (M3).

For the record, the progression I would otherwise have proposed — straight to frozen-attitude,
because that is what v1's fx27 port actually used — is **superseded**. The user's sequence is better
for this project's stated aim: it puts a closed-form-verifiable model first (M1 has an exact answer,
so the very first test checks real physics rather than its own output), and it introduces attitude as
a deliberate step instead of a precondition.

## 10. Non-functional decisions

**Determinism and reproducibility** (the foundation every regression test stands on):
- All randomness via an explicitly passed `numpy.random.Generator`, seeded from `Scenario.seed` (I3).
  No module-level `np.random` call anywhere — banned by the layering test.
- Every `SimulationResult` carries `provenance`: package version, `git describe`, `schema_version`,
  seed, model selection, integrator name and step size. A number without provenance is not a result.
- Floating-point policy: comparisons use explicit tolerances declared per test family
  (`analytic` 1e-10 relative on closed-form cases; `regression` 1e-8; `crosscheck_v1` 1e-6 absolute on
  apogee in metres, looser because v1's integrator differs; **`validation/fx27` looser again and
  oracle-dependent** — percent-level against another simulator's output, far looser against real
  flight data). Tolerances live in one `tests/tolerances.py` so loosening one is a visible diff, not
  a quiet edit. **No tolerance may be written inline in a test.**

**Performance budgets** — tests under `tests/perf/` (marker `perf`, excluded from the default run):

| Scenario | Budget | Why this number |
|---|---|---|
| Single 6-DOF flight, 60 s of flight, 1 kHz step | **< 2 s** | Must be fast enough that an fx27 run file feels interactive. |
| 1 000-member Monte Carlo, frozen-attitude, 100 Hz step | **< 60 s** | Dispersion analysis has to be runnable during a working session, not overnight. |
| Apogee-targeting optimization, ~50 inner flights | **< 60 s** | Closes the design loop while the user is still looking at it. |
| `import rocket_physics` | **< 150 ms** | Protects the TDD loop; also the canary for accidental module-level side effects. |

**Revisit trigger for D1 option B (Rust kernel) / `numba`:** if, after D3's vectorisation is in place
and profiled, the 1 000-member Monte Carlo budget is missed by more than 3×, the response is — in
order — (1) profile and fix the RHS allocations, (2) add `numba.njit` behind Seam 2 as an optional
extra, (3) only then consider a Rust kernel. Do not skip to (3).

**Parallelism:** none inside the core (I1/I4 keep it embarrassingly parallelisable from outside).
Process-level parallelism is a consumer concern, and vectorisation (D3) covers the common case.

**Scaling / concurrency:** out of scope by construction — this is an in-process library, not a
service. No DB, no queue, no cache, no sessions. If a results catalogue is ever wanted, that is a
separate stage with its own architecture round.

**Numerical robustness, decided now because retrofitting is painful:**
- The RHS must never raise on out-of-domain input (negative altitude, Mach beyond the aero table);
  it clamps and records a *warning channel* in the result (v1's `mach_warning.py` is the precedent).
  A Monte Carlo member that hits a table edge must not kill the run.
- Event detection by sign change plus bisection refinement to a declared time tolerance; events are
  recorded with the refined time, not the step time.
- Integrator failures raise `IntegrationError` with the state at failure attached — debuggability is
  part of the interface.

## 11. Rejected options

| Rejected | Why |
|---|---|
| Dual validation suites: anonymised fixtures here + the real suite in fx27 (my D6b recommendation) | **Rejected by the user.** fx27 has no test suite and will not get one (C8), so there is no second suite to defer to — the duplication layer would cost a permanent keep-two-sets-in-step tax for nothing. One suite, here, real numbers. |
| "2D" read as a planar *point mass* | Would make the 2D step a no-op: M1's dimension parameter already covers a planar point mass (§5.4). Flagged, not silently assumed. |
| Starting at frozen-attitude (what v1's fx27 port used) | Superseded by the user's point-mass-first progression, which is better: M1 has a closed-form answer, so the first test checks physics rather than the code's own output. |
| Julia core (D1 option C) | Technically the best numerics, but it orphans v1-as-oracle and fx27's existing Python material, and inverts the user's "build around fx27 first" plan. Deferred, not dismissed on merit. |
| Rust/C++ kernel now (D1 option B) | Premature: no measurement says the inner loop is the bottleneck yet, and it taxes every physics change. Kept reachable behind Seam 2. |
| Monolithic `schema.py` (v1's 28.4 KB) | Textbook shallow module: a huge interface over thin validation. Split per aggregate (§5.1). |
| `projects/` directory in this repo | Directly violates C1/C7 and is the identified v1 defect. |
| CLI / `__main__` / console entry point | Removed by the user (C5). Run files belong to fx27; adding a shell here would recreate v1's app-with-projects shape by the back door. |
| FastAPI/HTTP layer now | The user defined "API" as the package itself. No caller exists; honest HTTP for minute-to-hour jobs needs a job model, which is a stage of its own. |
| Plotting inside the physics modules (v1 had `plotting.py` and `report.py` in `engine/`) | Forces matplotlib into every import path and makes pure physics untestable without a display. Moved to an optional sidecar (D5). |
| Per-step `State` objects (OO trajectory) | Idiomatic-looking and 10-100× slower in Python; incompatible with D3's ensemble axis. Trajectories are arrays with named accessors. |
| A database for runs | Nothing needs it. Results are returned in memory; persistence is the consumer's choice. Revisit only if a results catalogue becomes a requirement. |
| `pint`/`astropy.units` for unit safety | Attractive, but unit-wrapped arrays are slow and leak into every signature. Replaced by I5 (SI-only core) + naming convention (`mass_kg`, `altitude_m`) + conversion at the edges. |
| Reusing v1 code | Explicitly a rewrite. v1 is read as an *oracle* (numbers) and as a *catalogue of mistakes*, never copied. |

## 12. Open questions — status

Resolved items are kept, marked, so nobody re-opens them. **Nothing here blocks RP-001.**

1. ~~What does "built as an API" mean concretely?~~ **RESOLVED 2026-11-27:** an importable Python
   package, nothing more exotic. No HTTP, no RPC.
2. ~~Is there a CLI / app shell in this repo?~~ **RESOLVED 2026-11-27:** no — not even as a reserved
   extension point. All run-shaped code lives in fx27.
3. ~~Relationship between this repo and `fx27`.~~ **RESOLVED 2026-11-27:** `fx27` is a *consumer*
   holding the run files that import this package and call Models / Simulations / Optimizations. Not
   a sibling effort, not a sub-repo, and no project *code* lands here.
4. ~~May fx27-derived reference numbers be committed here, or must validation live in fx27? Is fx27
   material confidential?~~ **RESOLVED 2026-11-27 (D6b, user override):** one suite only, here, in
   `tests/validation/fx27/`, with real fx27 numbers; no anonymised layer; not treated as
   confidential; fx27 has no suite of its own and will not get one. *(Sub-questions that lapsed with
   it: whether `simulation-3/` is the home of the new run files, and whether fx27 becomes its own git
   repo — both now fx27-side housekeeping, irrelevant to this repo's architecture. The dependency is
   an editable path install either way, D6a.)*
5. ~~Which dynamics model first — point mass, frozen-attitude, or 6DOF?~~ **RESOLVED 2026-11-27
   (D7, user-specified):** point mass → 2D → 3D. Translated in §5.4. Two residual ambiguities are
   flagged there rather than guessed: "2D" is read as a *planar rigid body with pitch* (not a planar
   point mass), and "3D" as *full 6-DOF* (with v1's frozen-attitude model available as an optional
   M2.5 if fx27 turns out to need exactly that). Neither blocks anything before RP-012; one sentence
   of confirmation from the user would close them.
6. **Is the LaTeX a port of v1's `dev/docs/latex-v2/` or a fresh document?** It already has the exact
   taxonomy and macros proposed in §8. If it is a port, the `docs/` tree should be seeded from it
   (copy, then prune) rather than written blank — and the user should confirm that copying v1's
   `.tex` into v2 is wanted, since everything else is a clean rewrite.
7. **Does the LaTeX↔code checker (§8.4) run as a blocking test or an advisory report?** Blocking is
   the whole point (the paper generates the backlog), but it means a freshly written `.tex` section
   makes the suite red until it is `\simtodo`-marked. Confirm the user wants that pressure.
8. **How is "stability" to be computed** — static margin from Barrowman geometry only, or dynamic
   stability (eigenvalue/damping analysis of the linearised system)? The second is a different
   mathematical apparatus and would add a `models/stability/` family plus its own `.tex`. It affects
   the stage-1 ticket list.
9. **Does the optimization side need gradients?** Gradient-free (`scipy.optimize` Nelder-Mead /
   differential evolution / bisection) covers apogee targeting and airbrake sizing. Gradient-based
   trajectory optimization would favour a differentiable stack (JAX/diffrax, or Julia), which would
   partly re-open D1. Worth one explicit answer now rather than a surprise in stage 3.
10. **Is `rocketpy` cross-validation wanted?** fx27's original `simulation` is `rocketpy`-based, so a
    third independent oracle is available cheaply. It would be a dev-only optional dependency.
11. **Which oracle supplies `tests/validation/fx27/`'s reference numbers?** *(New, created by the D6b
    override — needed for RP-009, blocks nothing before it.)* Four candidates exist in
    `D:/Projects - Ongoing/fx27`: (a) the 4 OpenRocket files in `open-rocket/`; (b) outputs of v1's
    port, `simulation-1/rocket_physics_port/runs/` — 7 entry points over the `cspace`/`euroc`
    campaigns with real motor CSVs; (c) the `rocketpy`-based original `fx27/simulation`; (d) real
    flight telemetry, if it exists. These are **different kinds of truth**: (a)–(c) are other models'
    opinions, so agreement is a consistency check and the tolerance is percent-level; (d) is reality,
    where disagreement means *our* model is wrong and the tolerance is set by instrumentation. Mixing
    them in one suite without labelling which is which is how a validation suite becomes
    meaningless, so RP-009 needs this answered — plus the vehicle/campaign to validate first, and
    which quantities count (apogee only, or the full trajectory, or also max-Q and rail-exit speed).

## 13. Environment facts (cached, do not re-probe)

Measured on this machine, 2026-11-27. Later rounds and the `developer` should take these from here
rather than probing again.

| Fact | Value |
|---|---|
| Python | 3.12.10 (only version on PATH) |
| NumPy | 2.5.4 — installed |
| SciPy | 1.18.1 — installed |
| matplotlib | 3.11.2 — installed |
| pytest | 9.1.1 — installed |
| uv | 0.12.17 — installed |
| numba, jax, pydantic, hypothesis, fastapi, pandas, polars | **not installed** |
| Rust / cargo | **not installed** |
| Julia | **not installed** |
| v1 declared deps (`requirements.txt`) | `numpy==2.5.4`, `scipy>=1.18,<2`, `matplotlib>=3.11,<4`, `pytest>=8` |
| v1 location (read-only reference) | `D:/Projects - Ongoing/rocket-physics` — engine at `apps/sim/engine/` (30 modules, 8 719 lines), tests at `tests/` (59 files), LaTeX draft at `dev/docs/latex-v2/` |
| fx27 location | `D:/Projects - Ongoing/fx27` — **not a git repo**; `simulation-3/` is empty |
| fx27 candidate reference data (for RP-009, §12 item 11) | `open-rocket/` — 4 `.ork` files (`fx27_cspace_01_03`, `fx27_cspace_02_01`, `fx27_cspace_03_01`, `fx27_euroc_01_03`); `simulation-1/rocket_physics_port/` — copy of v1's `projects/fx27` with `runs/` (7 entry points: `cspace_point`, `cspace_airbrake`, `cspace_comparison`, `cspace_ideal_drag`, `cspace_ideal_mass`, `euroc_comparison`, `euroc_sweep`), `data/motors/cspace/` (2 CSVs) and `data/motors/euroc-sweep/` (27 CSVs), plus `cspace/` and `euroc/` campaign configs (`motors.py`, `rockets.py`, `site.py`, `weather.py`, `scenarios.py`); `dossier-de-definition/` — the project definition dossier (LaTeX + PDF) |

Context7 was not reachable as a tool in this session, so no library-documentation lookups were
cached. All version facts above come from direct inspection of the local environment and of v1's
declared dependencies — primary sources, not recall. The one thing a later round may want from
Context7: pydantic v2's current recommended pattern for JSON Schema emission, and whether
`scipy.integrate.solve_ivp`'s event API has changed in 1.18.
