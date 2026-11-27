# Orchestrator: greenfield scaffold (new project / new major direction)

Read this before step one on a new project or a new major direction. Not needed for routine stage work — approval gates and the comparison-table template stay in `orchestrator.md`. Trackers: if `dev/status.json`, `dev/PROJECT-STATUS.md`, `dev/journal.md` do not exist yet, create them from `.claude/templates/` first.

## Complexity estimation (Estimation Gate)

After the initial discovery, `product-manager` is obliged to return an estimate of the project's complexity. **Do not start implementation before that estimate.** With the `concept` module active the estimate comes from product-manager's pass **after** the concept is accepted (working cycle, step 8): the accepted model is what gets estimated, not the brief as first written.

product-manager estimates by these criteria: the number of entities/integrations, the presence of complex business logic, scalability requirements, uncertainty in the requirements. Returns one of:

- `complexity: simple` — the project is small, the boundaries are clear, there are few risks.
- `complexity: complex` — the project is large, many dependencies, high uncertainty, or iterative delivery is required.

### Branch: simple

Implement the project **as fully as possible** without a breakdown into stages:
- The baseline market study has already run (it precedes the estimate) — the simple branch does not skip it. The same goes for the concept stage when its module is active: it runs before the estimate, in both branches.
- The full pipeline in one pass (after the brief, the concept and the estimate): `product → design track (if there is UI and the module is active) → architect → developer (+frontend-developer if there is UI) → qa + security → documentation`.
- The approval gates remain (brief, concept, design gates, stack, architecture, deploy).
- The finish: a working product + documentation.

### Branch: complex — MVP + stages

1. `product-manager` forms the **MVP scope** (the minimal valuable set of features) and the **stage plan** (Stage 1, Stage 2, …). Every stage is an independently launchable slice of the product with concrete deliverables.
2. Show the user the MVP scope and the stage plan through **AskUserQuestion**. Wait for an explicit "yes" on the scope and the order of stages — this is an approval gate. If a concept was accepted, show the scope **by concept screen ids** («MVP: S1–S6; стадия 2: S7, S8») and remind the user of the path to the model: they see what is in and what is later instead of imagining it.
3. Run the stages **sequentially**. Inside every stage:
   0. **Market triggers check** (`orchestrator.md` § «Market analysis → Task study»): a new user-facing feature area / `complex` stage → `market-analyst` `kind: task` first; its report path and registry ids go into the `product` prompt.
   a. `product` — the stage requirements + acceptance criteria. If a concept was accepted, pass `dev/concept/concept.md`: the requirements cover every concept screen in the stage scope.
   b. `architect` — architecture/changes for this stage.
   c. **Checkpoint:** show the user the technical decision points and the tool choice in the comparison table format (see `orchestrator.md` § "How to present technical decision points"). Wait for confirmation.
   d. If there is UI: the stage opens a new UI surface or a redesign → **design track** first (`.claude/docs/orchestrator-design.md`: variants on the board → user choice → the system grows); then `frontend-developer` agrees the patterns, citing `dev/design/DESIGN.md` → **user approval** → implementation. A screen that only follows approved patterns needs no new round.
   e. `developer` (then `frontend-developer`, as separate steps) — implementation. Several tickets from `task.md` — one at a time, sequentially.
   f. `qa`, then `security` — checking, one after the other.
   g. `documentation` — updating the documentation.
   h. **Closing the stage:** record the status in the tracker → **tracker archiving** (`archive_status.py --stages <id>` → `--apply`, see `orchestrator.md` § «Tracker archiving») → if the stage added a release step, a DB operation, or a data procedure, call `documentation` to update `dev/docs/release-runbook.md` → commit → **stage report** to the user: what was done, what is left, risks. Ask: continue to the next stage or adjust the plan?
4. Never move to the next stage without an explicit "yes" from the user.

## Kickoff: determining the scope (the FIRST step on a new project)

Before launching any agent, run a quick scope kickoff with the user. One exchange — and all subsequent steps go only through the needed modules.

**Step 1.** Ask for a short description of the task/project (1–3 sentences), if it has not been stated yet.

**Step 2.** Show the module checklist through `AskUserQuestion` with `multiSelect: true`:

```
Вопрос: «Какие модули нужны для этого проекта?
         Снимите галочки с тех, что не нужны или уже готовы.»

Варианты (все отмечены по умолчанию):
  ✅ vision             — разворот сырой идеи в полную картину (один раз, только новый проект)
  ✅ product-manager    — discovery, продуктовая карта, оценка сложности
  ✅ concept            — сырой кликабельный макет конечного продукта (не только MVP) до плана MVP: прокликать, поправить, добавить (после brief)
  ✅ product            — требования, user stories, acceptance criteria
  ✅ architect          — архитектура, стек, структура проекта
  ✅ developer          — реализация backend-кода
  ✅ design-track       — дизайн: бриф, варианты на доске, стиль, дизайн-система (только если есть UI)
  ✅ frontend-developer — реализация UI, design-sync, согласование паттернов
  ✅ qa                 — тест-кейсы, тестирование, дефекты
  ✅ security           — секреты, XSS, инъекции, права доступа
  ✅ documentation      — README, API docs, инструкции запуска
```

`market-analyst` is **not** on this checklist: the baseline study is mandatory and always runs (state it in one line under the question: «Анализ аналогов (market-analyst) выполняется всегда — это обязательный этап»). See `orchestrator.md` § «Market analysis».

**Step 3.** Record the chosen scope in the tracker (`status.json`, the `"active_modules"` field; `market-analyst` is always included). Skip the excluded agents in the working cycle — do not call them and do not wait for their outputs.

> **Rule:** if the user excluded a module another one depends on (for example, removed `architect` but kept `developer`) — warn them and ask for a deliberate confirmation.

`concept` stands for the concept stage (`concept-builder`; procedure — `.claude/docs/orchestrator-concept.md`) — record it in `active_modules` as `"concept"`. It needs neither UI nor a stack: a bot, a CLI or a service is shown through its interaction surface. Uncheck it only for a product with no human-facing behaviour at all (a pure library) or when the user already has a prototype they trust. Without `product-manager` it works from the vision and the user's description.

`design-track` stands for the four design agents (`design-researcher`, `design-explorer`, `design-critic`, `design-system-builder`) — record it in `active_modules` as `"design-track"`. Without UI, uncheck it. Without it `frontend-developer` works from its own Step 0 (`/frontend-design` + `ui-patterns.md`).

## Working cycle

1. **Kickoff** (see above) — determine the scope, record the active modules.
2. New project → `vision` (once, if it is in the active modules) — unfolds the idea into the vision brief (you pass the path to the agent; by default `dev/docs/vision.md`).
3. **Baseline market study — mandatory.** `market-analyst` with `kind: baseline` (vision path + output dir `dev/docs/market/`) → **Gate #0 — report review:** the absolute path to `baseline.html` + 3-5 takeaways + the analyst's questions → `AskUserQuestion` (accepted / add or fix analogues / go deeper) → revision rounds via `SendMessage` until accepted.
4. `product-manager` — **the brief only** (discovery → `project-brief.md`), if it is in the active modules. Inputs: the vision brief, `baseline.json` and `feature-registry.json` — MVP features are picked from the registry by id. With the `concept` module active, say so in the prompt: the product map, the stage plan and the estimate wait for the accepted concept.
5. **Gate #1 — Brief approval:** get the short project description from product-manager → show it to the user through AskUserQuestion → wait for an explicit "yes". Only after that do you move on.
6. Check/create the tracker (`dev/status.json`, `dev/PROJECT-STATUS.md`, `dev/journal.md` from `.claude/templates/`); register `market_baseline` and `feature_registry` paths in `artifacts`. The tracker is created at kickoff at the latest — this step is a re-check.
7. **Concept stage** (module `concept` active — otherwise skip to step 8). Read `.claude/docs/orchestrator-concept.md` and follow it: `concept-builder` builds the raw clickable model from the approved brief → you check it and give the user the path, the builder's assumptions and the scenarios → rounds on the user's remarks (same builder, `SendMessage`; every remark into `dev/concept/feedback.md` first) → **Gate — concept accepted** (explicit «принята») → commit. No tests, QA, security, architect or design agents here.
8. `product-manager`, second pass (**estimation**): the product map, registry decisions, the stage breakdown, `complexity`. After a concept — `dev/concept/concept.md` and `feedback.md` are mandatory inputs: it syncs `project-brief.md` with the accepted model (returns `brief_changes_ru`) and cites concept screen ids in the stage scope. Changed «Ключевые функции MVP» / «Вне scope MVP» lines → show them to the user and get a "yes" before the estimate is used.
9. **Estimation Gate:** take `complexity` from that pass → choose the simple / complex branch.
   - Simple → the full pipeline (active modules only).
   - Complex → show the MVP + the stage plan → get approval → go stage by stage.
10. Delegate the next step per the scope **from the active modules**, passing the context. With `design-track` active and a UI in scope: after `product` — the design track (R0 brief → structure → style → `DESIGN.md`), each step a user gate in the browser; `architect` gets `dev/design/DESIGN.md` as an input (UI library and styling choice must fit its tokens). After a concept, `product`, the design track, `architect` and `frontend-developer` also get `dev/concept/concept.md` as the reference of what exists and where it leads (`orchestrator-concept.md` § C5).
11. **Gate #2 — Stack and architecture approval:** after architect → a comparison table → AskUserQuestion → wait for a "yes".
12. Get the JSON, process the decisions/approvals through the user.
13. Update the tracker.
14. Repeat. On completion of a stage (complex) or of the whole project (simple) — a report + a proposal for the next step (with approval) + recording in the tracker + a proposal to run `/compact` (see `orchestrator.md` § "Compact after a block").

Use TodoWrite for a visible plan: mark the current stage and branch (simple/complex).
