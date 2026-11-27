# Experiment track — procedure for the orchestrator

Cold document: read it when you are about to offer an experiment (E0) or the user ran `/experiment`, not on every turn.

## Why this track exists

On a working product every change goes through the full pipeline: requirements, TDD, QA, security, several rounds of reports. That is the right price for code that stays — and the wrong price for an idea the user has not tried yet. Half of such ideas change shape the moment the user sees them on real data, and some are dropped. The track splits the work in two: **a quick version first** — real code, the user's real data (a copy), no tests and no reviews — the user tries it and decides; **the full pipeline only after «оставляем»**, rebuilding the change properly with the accepted behaviour as its acceptance criteria. The saving is on everything that changes or gets dropped after the first look.

## Five rules that override everything else here

1. **Ask, never assume.** You offer the experiment and start it only after the user's explicit «да» (E0). `/experiment` is that «да».
2. **Fast and rough.** `experimenter` alone. Never spawn `qa`, `security`, `architect`, `product`, the design agents or `documentation` on an experiment, and never ask it for tests or "proper" code.
3. **The experiment's code never reaches the base branch.** Not "after a quick cleanup", not "it already works, let's keep it". Only two exits: «оставляем» → the full pipeline rebuilds it in a new tree; «выбрасываем» → the tree is dropped.
4. **The user judges by using it.** Your message is how to start it and what to try — not a retelling.
5. **The real data is never touched.** The experiment runs on an isolated copy; when there is no isolation, the user hears that before anything starts.

## Place in the kit's process

`user's request → [E0: «сначала быстрая версия?»] → experimenter (rounds) → [E5: оставляем / выбрасываем] → оставляем: product → (architect) → developer/frontend-developer (TDD) → qa → security → land gate`

- **Only on a working product** — at least one stage landed, the product runs. Before that the concept stage (`orchestrator-concept.md`) answers "is this the product I meant?"; an experiment answers "does this change work for me on my data?".
- **Not the concept.** The concept is a throwaway model on fake data before any code; an experiment is the product's own code on real data.

## E0 — When to offer, and how

**Offer** when the user brings a task that changes what they see or how they work: a new feature, a new screen or report, a changed flow or rule, a new field carried through the product. In a stage with several such features — one question for all of them (`multiSelect`: which to try first).

**Do not offer** for: bug fixes, security fixes, refactoring, dependencies, infra/deploy, documentation, performance; a task that is the full version of an accepted experiment; a change the user already specified to the last detail and said "just do it"; changes that need an architectural decision first (new service, storage, integration — the experiment would build debt, not an answer).

**Opt-out.** If the user says to stop offering (`не предлагай эксперименты`) → a `decisions` line `experiment-offers: off` and you stop; `/experiment` still works. Check it before offering: `status_query.py decisions --grep experiment-offers`.

**The question** — `AskUserQuestion`, one question, after you have understood the task and before any other delegation:

- «Сначала быстрая версия (рекомендую)» — description: «за один проход, на копии ваших данных, без тестов и проверок; попробуете и решите — оставить, поправить или выбросить. Если оставляем — делается заново по полному циклу».
- «Сразу полная реализация» — description: «обычный цикл: требования, TDD, QA, security».

Put «(рекомендую)» on the experiment when the task leaves the user's intent open (how it should look or behave, whether it pays off); on the full implementation when the task is small and fully specified. The answer → a `decisions` line.

## Files

```
dev/experiments/<slug>/
  experiment.md          # RU — how to run, what to try, shortcuts, assumptions, tests, rounds. Written by experimenter.
  feedback.md            # RU — the user's remarks per round, verbatim, and the decision. Written ONLY by you.
  experiment.patch       # the experiment's diff, saved on «оставляем» — a reference for the full version
  experiment-notes.md    # EN — the experimenter's handover notes (only when its context is handed over)
```

While the experiment runs, the folder lives in the experiment's worktree. It reaches the base branch only inside the full version's tree after «оставляем» (E5) — never with the experiment's code.

## E1 — Prepare

**Worktree mode on** (`CLAUDE.md` § «Профиль проекта»):

1. `python .claude/scripts/wt.py new exp-<slug> --task "experiment: <one line>"` — the default `--db copy` gives the tree its own copy of the real database.
2. Read the `DATABASE`/isolation line of the output. `isolated` → go. Anything else (the project has no isolated database, `share`, `failed`, a data file linked from the main repo) → tell the user in two lines that the experiment would work on the **real** data and that schema changes are off; `AskUserQuestion`: «Продолжить без изменений схемы» / «Отменить эксперимент». `failed` → `wt.py doctor`, fix the isolation, do not continue on a broken tree.

**Worktree mode off:**

1. `git status` — the tree must be clean (otherwise ask what to do with the changes).
2. `git switch -c exp/<slug>`.
3. There is no data isolation: say so, offer a backup copy of the database / data file first, and the same «Продолжить без изменений схемы» / «Отменить» question. The experimenter's prompt then carries `DATABASE: shared with the real product — no schema changes, no destructive writes.`

Then `status.json → decisions`: `experiment:<slug>` started, with the tree/branch name.

## E2 — Build

Spawn `experimenter` (one agent). The prompt carries:

- the `wt.py prompt --slug exp-<slug>` block (or, with worktree mode off, the repo path + the `DATABASE:` line above);
- the user's request **verbatim**, plus your reading of it in 1–3 lines;
- the experiment folder `dev/experiments/<slug>/`;
- pointers: the relevant architecture slice (file + section), `dev/design/DESIGN.md` if it exists, the requirements ids the change touches if you know them;
- if another tree is running a full test suite — say so (one full suite per machine).

Nothing about tests, quality or structure — the persona already says what is out.

## E3 — Show

1. Read the reply. `tests` lists failures that are not the requested behaviour change, or `self_check` says it was not run → back to the experimenter via `SendMessage`, not to the user.
2. `wt.py commit --slug exp-<slug> -m "experiment(<slug>): round 1"` (worktree off: `git add -A && git commit` on `exp/<slug>`) — the round survives a lost session.
3. Message to the user, in this order:
   - **Как запустить:** `how_to_run_ru` as is. Offer to start it for them — you may run the start commands with `run_in_background` on the tree's ports and give the URL.
   - **Что попробовать:** `try_ru`.
   - **Что я додумал сам:** `assumptions_ru`.
   - **Сделано на скорую руку:** `shortcuts_ru` — so a rough edge is not mistaken for the design.
   - Schema changes and failing tests, if any, in one line each.
4. `AskUserQuestion`: «Оставляем — делаем полную версию» / «Есть правки» / «Выбрасываем». The descriptions say what happens: the full pipeline in a new branch and the experiment branch deleted; another quick round; the branch and its database deleted, the idea recorded in the journal.

## E4 — Rounds

1. **Write the remarks into `dev/experiments/<slug>/feedback.md` first, verbatim** (`### Раунд N — <date>`, the user's words, your one-line reading of ambiguous ones). It lives in the experiment's tree; you write it there.
2. `SendMessage` to the same experimenter: the remarks verbatim + your readings. Chain-break rules of `orchestrator.md` (context ≥ 200k, long pause, `/compact`) → a fresh spawn with `experiment.md`, `feedback.md`, `experiment-notes.md`.
3. Back to E3.

These rounds are the user's own — the three-round cap does not apply. Watch for drift instead: rounds that keep adding scope or start asking for robustness ("а если ошибка…", "а права…") mean the idea is accepted and the user now wants the real thing → offer «Оставляем — делаем полную версию».

## E5 — Decision

### «Оставляем»

1. Append the decision to `feedback.md`: `## Решение — оставляем (<date>)` + the user's words + «Принятое поведение — `experiment.md`, раунд N». Commit the round in the experiment tree.
2. Open the full version's tree: `wt.py new <slug> --task "<one line>"` (from the base, not from the experiment).
3. Carry the reference over — the experiment tree and the new tree are both outside the main repo:
   `cp -r <exp-tree>/dev/experiments/<slug> <new-tree>/dev/experiments/` and
   `git -C <exp-tree> diff origin/<base>...HEAD -- . ':!dev/experiments' > <new-tree>/dev/experiments/<slug>/experiment.patch`.
   Worktree off: `git switch <base>`, then the same files from the experiment branch (`git show exp/<slug>:dev/experiments/<slug>/experiment.md > …`, `git diff <base>...exp/<slug> -- . ':!dev/experiments' > …/experiment.patch`).
4. Drop the experiment: `wt.py drop --slug exp-<slug> --force` (the user's «оставляем» was the go-ahead — the question said the branch is deleted), then the `dbdrop` line it prints. Worktree off: `git branch -D exp/<slug>`.
5. `decisions`: `experiment:<slug>` → kept, round N. Then the **normal pipeline** in the new tree, by the project's usual rules:
   - `product` gets `experiment.md` + `feedback.md`: § «Что попробовать» (final round) and the user's words become acceptance criteria; **every** line of § «Сделано на скорую руку» is either covered by a requirement or explicitly dropped with the user; § «Допущения» the user did not confirm are open questions, not accepted behaviour.
   - `architect` only if the shortcuts list or the patch holds a real architectural question.
   - `developer` / `frontend-developer` — TDD as always: tests first, against the accepted behaviour; `experiment.patch` is a map of where the change lives, not code to apply.
   - `qa`, `security`, `documentation`, the land gate — unchanged. `dev/experiments/<slug>/` lands with the full version and stays as its history.

### «Выбрасываем»

1. Ask for one line of why, if the user did not say it — a cheap «нет» is the track's value only if the reason survives.
2. `dev/journal.md`: `### <date> — Эксперимент <slug> отклонён` — what was tried (2 lines), the user's reason, round count. `decisions`: `experiment:<slug>` → dropped.
3. `wt.py drop --slug exp-<slug> --force` + the printed `dbdrop`. Worktree off: `git switch <base>`, `git branch -D exp/<slug>`.

## One home per fact

| Fact | Home |
|---|---|
| What the experiment does, how to run it, shortcuts, assumptions | `experiment.md` (experimenter) |
| The user's remarks and the decision | `feedback.md` (you) |
| Started / kept / dropped | one `decisions` line each in `status.json` |
| Why a dropped idea was dropped | `dev/journal.md` (the experiment's files are gone with its branch) |

## Language

Everything the user reads — your messages, `experiment.md`, `feedback.md`, the journal entry — Russian by default. Delegation prompts and the experimenter's replies — English; its `*_ru` fields you show as is.
