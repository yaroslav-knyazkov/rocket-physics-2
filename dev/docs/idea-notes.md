# Raw idea notes — input for `vision` / `product-manager`

Captured verbatim from the user's kickoff message (2026-11-27). Not a finished vision or brief — this is the raw source material those agents consume and formalize. Do not treat as an approved spec.

## What the app is

A rocket solver: software for rocket trajectory and stability simulation, control implementation and optimization. This is **version 2** of an existing tool, `rocket-physics-1`.

## Lessons from v1 (rocket-physics-1)

- v1 had **projects built directly into the app** — project-specific code was embedded in the application itself rather than the app being a general-purpose tool consumed by projects.
- The biggest issue with v1: **everything was built first, then tested** (build-then-test, not test-driven). This is explicitly called out as the thing to avoid in v2.
- v1 had LaTeX documentation describing the physical/mathematical models — referenced as prior art for v2's "Models" concept.

## v2 approach

- **Architecture shift: built as an API.** The core is a library/API consumed by external projects, not an app with projects baked in.
- **Development order is inverted from v1 on purpose:** this time, build the app **around one real project first**. Only once that project works end-to-end does the app get generalized/extended for other projects. (Rationale: avoid repeating v1's build-everything-then-test mistake — ship something real and tested early, generalize later.)
- **End-state shape (later, not now):** a GUI application organized around three top-level concepts — **Models**, **Simulations**, **Optimizations** (same structure/terminology as the LaTeX docs in v1 — see v1 LaTeX for the model taxonomy to carry over).
- **Current phase:** console app (no GUI yet). GUI is a later extension on top of the same core/API, not part of the initial build.

## User's own rollout plan (as stated, not yet validated by architect)

1. Write the LaTeX first (formalize the physics/math models — the same role the v1 LaTeX docs served).
2. Build the core in this repo (`rocket-physics-2`, this folder).
3. The driving real project lives in a **separate folder**: `D:\Projects - Ongoing\fx27`. The core is built/tested against this concrete project before being generalized.

## Open questions this raises (for vision / architect, not resolved here)

- ~~Exact relationship between this repo (core/API) and `fx27` (the driving project): is `fx27` a consumer of the API (separate repo depending on this one), or is it a parallel/sibling piece of work that informs requirements? Needs clarifying with the user during `vision`/`architect`.~~ — **решено, см. «Уточнения пользователя» ниже.**
- ~~API language/stack not yet decided — v1's stack is unknown to this note; `architect` should ask or check if v1 source is available for reference (not for reuse, just for "what to avoid").~~ — **решено: Python 3.12 + NumPy/SciPy, гейт пройден 2026-11-27.** v1 оказался на Python 3.12 (numpy 2.5.4 / scipy 1.18 / pytest), исходники доступны только для чтения как численный эталон. Разбор — `architecture-stage1.md` §2, §3, §9 D1.
- Scope of "Models" / "Simulations" / "Optimizations" taxonomy should be pulled from v1's LaTeX once the user writes/shares it, not guessed. — *частично закрыто:* каркас разделов взят из `latex-v2` v1, соответствие LaTeX ↔ код — `architecture-stage1.md` §8; содержание формул пишет пользователь.

## Уточнения пользователя (решено, 2026-11-27)

Записано оркестратором со слов пользователя в ходе этапа архитектуры. Отменяет соответствующие пункты выше.

- **Связь с `fx27` — закрыта.** Этот репозиторий (`rocket-physics-2`) и есть ядро, оформленное как пакет/библиотека; именно это и означает слово «API», ничего более сложного. В `D:\Projects - Ongoing\fx27` лежат **файлы запуска** — проектные скрипты, которые импортируют этот пакет и вызывают Models / Simulations / Optimizations. `fx27` — потребитель пакета, а не параллельная работа и не подрепозиторий. Проектного кода внутри `rocket-physics-2` быть не должно — это подтверждает вывод из опыта v1 (никакого встроенного кода проектов).
- **CLI полностью снят из области работ.** Дословно: «please dont define CLI too». В этом репозитории не проектируется, не упоминается и не закладывается никакой CLI / слой приложения — даже как «точка расширения на будущее». Ядро — исключительно импортируемый пакет. Любой код формата «запуск / точка входа / CLI» живёт в `fx27`, за пределами этого репозитория. Цель разделения (чистый тестируемый физический код отдельно от всего остального) сохраняется, но отделять его от оболочки не требуется — оболочки здесь просто нет.
- Следствие для пункта «Current phase: console app» в разделе «v2 approach» выше: формулировку «console app» читать как «только импортируемый пакет, без GUI», а не как «консольное приложение с CLI».
- **Валидация по fx27 — один набор тестов, и он внутри `rocket-physics-2`:** `tests/validation/fx27/`, на настоящих эталонных числах fx27, без промежуточного слоя обезличенных фикстур (архитектор предлагал два набора — пользователь отклонил). У fx27 своих тестов нет и не будет. Это единственное исключение из правила «ничего проектного здесь»: проектные **данные** — только в этой папке, проектный **код** — нигде. Подключение пакета в fx27 — editable-установка по пути (`uv pip install -e …`); переход на колесо с зафиксированной версией — когда число из ядра впервые попадёт в отчёт или LaTeX.
- **Порядок усложнения модели динамики (слова пользователя):** «first we start with point mass, then 2D, then 3D». Перевод в конкретные модули, состояния и порядок тикетов — `architecture-stage1.md` §5.4 (там же помечены два места, где слова «2D» и «3D» допускают два чтения; взято наиболее естественное, работа не заблокирована).
