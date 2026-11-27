# Concept stage — procedure for the orchestrator

Cold document: read it when the concept stage starts (after Gate #1 on a new project, or `/concept`), not on every turn.

## Why this stage exists

The failure it prevents: the team reads the brief one way, the user meant another, and the difference surfaces after the whole pipeline has run. A text the user approved is not proof that both sides picture the same product. So before the MVP is planned, the user gets a **raw clickable model of the final product** — screens, transitions, the main scenarios working on fake data — clicks through it and corrects it. The final product, not the MVP: when the MVP does by hand what the product will automate later, a model of the MVP shows the chore instead of the idea. Later-stage parts are simulated on canned data and tagged «этап N». A wrong reading costs one round here instead of a stage later.

## Four rules that override everything else here

1. **Fast and raw.** Minutes, not hours. No tests, no QA, no security review, no code review, no architect, no design, no documentation pass on the model — never spawn those agents on it, and never let the builder "do it properly". The model's code is thrown away.
2. **The user judges by clicking, not by reading.** Your message is a pointer to the model: where to open it, which scenarios to walk, what was assumed. Do not retell screens in chat.
3. **Assumptions first.** What the builder decided on its own is exactly where the misunderstanding hides. Show the assumptions before anything else and ask the user to look at those screens first.
4. **Rounds are cheap, so take them.** The user says what to add or change → the same builder edits the model → the user looks again. The stage ends only on the user's explicit «концепция принята».

## Place in the kit's process

`vision → market-analyst → product-manager (brief) → [Gate #1: brief approved] → **concept** → [Gate: concept accepted] → product-manager (brief sync, product map, stages, complexity) → Estimation Gate → …`

- **Runs when** the kickoff module `concept` is active (`status.json → active_modules`; on by default). A project whose result has no human-facing behaviour at all (a pure library) — propose unchecking it at kickoff.
- **Before the MVP is fixed, on purpose.** The model shows the picture of the *product*; which part of it becomes the MVP is decided at the next gate, with the model in front of the user. Do not ask `product-manager` for the stage plan before the concept is accepted.
- **Inputs:** `dev/docs/project-brief.md` (approved), `dev/docs/vision.md`, `dev/docs/market/feature-registry.json`. No `product-manager` in the active modules → the builder works from the vision and the user's description.
- **Later in a project's life** — only by `/concept <what>` or when you proposed it in one line and the user said yes (a new major direction, a large feature area with new screens): «Перед этим направлением могу собрать кликабельную концепцию — посмотреть до разработки. Собрать?». Never on your own, never for a fix or an incremental feature.
- **Not the design track.** The concept decides *what exists and where it leads*; the design track decides *how it looks*, in variants on the board. A remark about colours, fonts or composition during the concept → record it in `feedback.md` under «Для дизайн-трека» and tell the user it will be decided there, on real variants; the builder does not act on it.

## Files

```
dev/concept/
  concept.md        # RU — screen map, scenarios, assumptions, stubs, version log. Written by concept-builder.
  feedback.md       # RU — the user's remarks per round, verbatim. Written ONLY by you.
  concept-notes.md  # EN — the builder's handover notes (only when its context is handed over)
  app/              # the model: index.html, concept.css, concept.js (kit, untouched), data.js, screens*.js
  shots/            # self-check screenshots (gitignored)
```

The first concept of a project lives in `dev/concept/`. A later one (another direction) — in `dev/concept/<slug>/` with the same layout; pass that folder to the builder and to `concept-check.mjs`.

## Steps

### C0 — Prepare

1. `dev/concept/app/` does not exist yet → copy the starter kit (a copy of kit files, one command):
   `mkdir -p dev/concept && cp -r .claude/templates/concept-app dev/concept/app`
2. `current_stage` / `next` in the tracker: concept in progress.

### C1 — Build

Spawn `concept-builder` (one agent, foreground or background). The prompt carries: the concept folder; the paths of the brief, the vision and the feature registry; the product's language; when worktree mode is on — the `wt.py prompt` block. Nothing about stack, tests or quality. Do not paste the brief's text — the builder reads the files.

While it builds, tell the user in two lines what is coming: a raw model, opened by double-click, grey on purpose.

### C2 — Check and show

1. Run the check yourself — a model that opens broken must never reach the user:
   `node .claude/tools/concept-check.mjs dev/concept/app` → `CHECK OK`. Errors → back to the builder through `SendMessage` with the output, not to the user. Exit 2 (no browser on the machine) → say so and show the model anyway.
2. Message to the user, in this order:
   - **Open:** the absolute path to `dev/concept/app/index.html` — double-click, no server. In the top bar: «Карта экранов» lists every screen with its ID and the scenarios.
   - **Что я додумал сам — посмотрите в первую очередь:** the builder's `assumptions_ru`, as is.
   - **Пройдите сценарии:** `scenarios_ru`.
   - **Как читать модель:** it is grey and rough on purpose — the look is decided later; it shows the finished product, and a tag «этап N» marks what comes after the MVP (it works here on prepared data); a dashed frame is a stub (drawn, not working); data is fake and resets with «Сбросить данные».
   - **Как отвечать:** in plain words, naming screens by ID — «на S3 не хватает…», «S5 лишний», «после S2 я ждал другого». Missing screens and missing steps are the most valuable remarks.
   - `questions_ru`, if any.
3. `AskUserQuestion` — one question: «Концепция принята — идём дальше» / «Есть правки» / «Идея понята неверно». Free text is always available; the user may simply write the remarks.

### C3 — Rounds

On remarks:

1. **Write them into `dev/concept/feedback.md` first, verbatim** (format below) — the dialogue is disposable, the file is not.
2. A remark you cannot place on a screen → one clarifying question, then go.
3. `SendMessage` to the same builder: the remarks verbatim + your one-line reading of each ambiguous one. A new spawn only when the chain must break (`orchestrator.md` § «Continuing an agent…»: context ≥ 200k, a long pause, `/compact`) — then the new builder gets `concept.md`, `feedback.md` and `concept-notes.md`.
4. Back to C2: check, then show **what changed** (`changed_ru`), the new assumptions, and ask again.

The three-round cap of `orchestrator.md` does not apply here: these rounds are the user's own, each one moves the model towards what they meant. What to watch instead:

- **The same screen reworked three times** → the trouble is below the screen. Ask what the user is trying to achieve there, not what to move.
- **Remarks keep adding features** → that is the stage doing its job, not scope creep. Do not push back; tell the user once that the model may hold more than the first version will — what goes into the MVP is decided at the next gate.
- **«Идея понята неверно»** → do not rebuild blindly. Ask what is wrong at the level of the idea (for whom, what the main thing is, what the result of using it looks like), record it in `feedback.md`, then decide by the answer: a detail of the brief → `product-manager` fixes `project-brief.md` → the user confirms the changed lines → the builder reworks the model from the new brief; the picture itself is off → propose returning to `vision` (the user decides). Two «неверно» in a row → the input is wrong, not the model: go back to the brief or the vision before a third build.

`feedback.md` entry:

```markdown
## v1 → v2 — 2026-11-19
Слова пользователя: «на S3 нужен фильтр по дате, S5 вообще не нужен, и где отчёт за неделю?»
Разбор: S3 — фильтр по дате · S5 — убрать · новый экран: отчёт за неделю
Меняет brief: да — новая функция «отчёт за неделю»; убрана «…»
Для дизайн-трека: —
```

The «Меняет brief» line is what you hand to `product-manager` after acceptance — keep it exact.

### C4 — Gate: the concept is accepted

Only on the user's explicit «принята». Never infer it from silence or from «выглядит неплохо, но…».

1. `status.json → decisions`: `{"topic": "concept", "choice": "принята, v<N>; <one line: what changed against the brief, or «без изменений brief»>", "author": "user", "user_approved": true}`; `artifacts`: `concept` → `dev/concept/concept.md`, `concept_app` → `dev/concept/app/index.html`.
2. The builder's final turn (through `SendMessage`): set «Статус: принята <date>» in `concept.md`, remove the in-progress marker if it is still there.
3. Commit `dev/concept/` like any deliverable.

### C5 — Sync back and hand over

1. **`product-manager`, next pass** (the one that follows Gate #1 anyway: product map, registry decisions, stages, complexity) gets `dev/concept/concept.md` and `dev/concept/feedback.md` as mandatory inputs:
   - it brings `project-brief.md` in line with the accepted model and returns the changed lines (`brief_changes_ru`);
   - features born in the concept go into the registry (`origin: "user"`);
   - the MVP scope and the stage plan cite concept screen ids («MVP: S1–S6; стадия 2: S7, S8»).
2. **Brief changes go back to the user.** «Ключевые функции MVP» or «Вне scope MVP» changed → show the changed lines and get a «да» (`AskUserQuestion`) — it is the same Gate #1 fact, updated. Other lines changed → inform in one line.
3. Then the Estimation Gate as usual (`orchestrator-greenfield.md`). In the complex branch show the MVP scope **with the screen ids** — the user has the model open and sees what is in and what is later.
4. **Downstream agents get the concept as a reference of behaviour** — the path to `concept.md` (and to `app/` where noted), with the same line every time: *"the concept fixes what exists and where it leads; its code and its look are not a source of anything."*
   - `product` — `concept.md`: requirements cover every concept screen in the stage scope.
   - design track — `concept.md` § «Карта экранов» is the list of screens for the R0 brief and the lo-fi structure rounds; the model's grey layout is **not** a structure proposal.
   - `architect` — `concept.md` and `app/data.js` (the entities the user has seen); the stack is chosen from the requirements, never from the model's code.
   - `frontend-developer` — `concept.md` + the model itself to click: screens, transitions, what each control does.

After acceptance the model is frozen: it is not kept in sync with the product. A later change of direction is a new `/concept` round, not maintenance.

## Worktree mode and commits

While `.claude/wt-active.json` exists the main repo is read-only (hooks). On a new project the concept runs before any task worktree exists — nothing special. A later concept: run it before the task worktree is created, or inside it (then `dev/concept/…` lives in the worktree and every path you quote is a worktree path).

## Delegation — lines you owe the builder

- The concept folder and the input paths.
- First build: nothing else. Do not add wishes about quality, structure or stack — they slow the model down and the persona already forbids them.
- Revision: the user's words verbatim; your reading of the ambiguous ones; «do not touch screens the user did not mention».
- Reply short: the status JSON; the detail is in `concept.md`.

## Language

Everything the user reads — your messages, `concept.md`, `feedback.md`, the visible text of the model (the product's language) — Russian by default. Delegation prompts and the builder's replies — English; its `*_ru` fields you show as is.
