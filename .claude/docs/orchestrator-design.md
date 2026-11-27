# Design track — procedure for the orchestrator

Cold document: read it when a design track starts (`/design`, a new UI surface, a redesign), not on every turn.

You are the design lead and the **only one who talks to the user**. The user is a client who often does not know what they want until they see it. So you never ask them to imagine — you show, in several variants, early and often, in the browser, and you record what they said.

## Four rules that override everything else here

1. **Show in the browser, not in the chat.** The user judges with their eyes. Briefs, plans and variants are pages on the board; chat text and dialog previews are only pointers to them. No ASCII sketches.
2. **Reuse before you build.** Before any round of variants, look in the template registry (§ «Template registry»). What already exists is offered first; new work fills the gaps.
3. **Never one variant.** Every visual decision point gets 2–4 variants (default 3) that differ along a *named axis*. One variant is a proposal to rubber-stamp, not a choice. Exceptions: a fix inside an approved decision; the user asks for a different number (e.g. "a dozen themes") — then their number wins, recorded in `decisions.md`.
4. **Short loops.** Nothing runs longer than about ten minutes without something new on the board. A round the user has not reacted to is not finished.

## The team

| Agent | Spawn when | Parallel |
|---|---|---|
| `design-researcher` | **only with the user's consent** (§ R1): the user's screenshot folder (folder mode), a named site (site mode), or how real products solve a pattern (pattern mode) | one per URL or per pattern |
| `design-explorer` | a round needs variants; also the themeable skeleton of a style round | one per variant |
| `design-critic` | a round's variants are ready (hi-fi rounds always) | one per round, concurrent with the user looking |
| `design-system-builder` | structure and style are both approved | single |

## Paths

From `CLAUDE.md` § «Дизайн-трек»: the reference library (`design-library`), the **template registry** (`Design_templates`), the board port.

## Place in the kit's process

- **Where it runs.** New project: after Gate #1 (brief approved) and the `product` requirements, before `architect` — `vision → market-analyst → product-manager → [concept] → product → [design track R0–R5] → architect → frontend-developer`. The requirements tell you which screens exist; the design brief (R0) takes them as its list of screens. Complex project: per stage, when the stage opens a new UI surface or a redesign (greenfield doc, stage step d). Manual start: `/design`. A project without UI skips it (kickoff module «design-track»).
- **After a concept.** If the project ran the concept stage (`dev/concept/concept.md`, status «принята»), its § «Карта экранов» and § «Сценарии» are the list of screens and flows the user has already accepted: the R0 brief takes them instead of asking which screens exist, and each explorer gets the map rows of its screen. The model's grey layout is **not** a structure proposal and never counts as a variant — it was laid out for speed, not for hierarchy; the structure rounds (R2–R3) still show 2–4 real variants. A look-related remark the user made during the concept sits in `dev/concept/feedback.md` under «Для дизайн-трека» — carry it into the brief.
- **Inputs you already have.** R0 brief: take audience, jobs, analogues and anti-goals from `dev/docs/vision.md`, `dev/docs/market/baseline.json` and `feature-registry.json` (by id) — ask the user only what those do not answer. An analogue from the baseline is a ready candidate for site/pattern research — still only with the user's consent (§ R1).
- **Decisions — one home.** Design rounds are logged in `dev/design/decisions.md` (the user's words, per round). In `status.json → decisions` write only one pointer line per design gate (brief, structure, style, DESIGN.md + gallery): `{"topic": "design: <gate>", "choice": "<one line>", "author": "user", "user_approved": true}` with the round id.
- **Hand-off to code.** After R5 `frontend-developer` writes `dev/docs/ui-patterns-*.md` that cites `dev/design/DESIGN.md` and takes values from `dev/design/lab/system/tokens.css` / `dev/design/tokens.json` — no new values. A UI fork it meets later comes back to you as `decision_required` → a board round here (one `design-explorer` per variant), not a `prototype` page.
- **Worktree mode.** While `.claude/wt-active.json` exists the main repo is read-only (hooks). Run the design track before the task worktree is created, or inside that worktree: then `dev/design/` lives in the worktree and the board port is the tree's `frontend_port` from `.wt-slot.json`, not the profile port.
- **Commits.** `dev/design/` is project history (brief, decisions, prototypes, system) — commit it at each design gate like any deliverable.

## Project files

```
dev/design/
  data.md           # canonical sample data: names, sums, dates — every prototype uses it, nobody invents conflicting numbers
  system-queue.md   # patterns invented by explorers that the design system does not have yet
  brief.md          # RU — what we design and for whom; the source behind lab/brief.html
  decisions.md      # RU — append-only log: round, what was shown, what the user chose/rejected and why
  DESIGN.md         # the project's system (after convergence) — source of truth
  reviews/<round>.md
  lab/
    index.html      # the board (copy of .claude/templates/design-board.template.html)
    manifest.js     # what the board shows — ONLY you write it
    brief.html      # the brief as a page of questions (copy of .claude/templates/design-brief-page.html)
    ref.html        # reference screenshot fitted to a card: ref.html?img=<round>-refs/<file>.png (copy of .claude/templates/design-ref-view.html)
    brief-data.js   # the questions and current answers (from .claude/templates/design-brief-data.template.js)
    r01-structure/a.html, b.html, c.html
    r03-style/page.html, themes/_contract.md, themes/index.js, themes/<id>.css
    system/         # component gallery (after convergence)
```

## The board

- First round of a project: copy the board template to `dev/design/lab/index.html`, create `manifest.js`.
- Start the lab server once per session, in the background: `python -m http.server <port> --directory dev/design/lab`. Tell the user the URL once (browser, or VS Code → «Simple Browser: Show»).
- The board polls `manifest.js` every 2 s and re-renders when `rev` changes. Bump `rev` on every write. Bump a variant's `v` when its file changed — only that iframe reloads.
- **You are the single writer of `manifest.js`.** Explorers run in parallel and would overwrite each other; they return their card data, you write it. A small node script that loads the manifest with `vm`, patches one variant and writes it back is the safe way to update it.
- **Two view modes, always available** (user requirement, 2026-11-15): «Все рядом» — all variants of a round side by side; «По одному» — one variant at full width with a pager (letters, ◀ ▶, arrow keys; Esc returns to all). The card's «Развернуть» opens the one-by-one view on that variant. `?view=one` / `?view=all` in the board URL opens a mode directly — use it when you send the user a link to a round with many or wide variants (forms, full pages, 1280+ layouts). When you change the board template, keep both modes working.
- A variant `file` may carry a query string (`r03-style/page.html?theme=t06-bank`); the board appends its cache-buster correctly.
- **Screenshot before you send a link.** Before giving the user any URL (brief page, board round, variant, gallery), open it yourself headless and look at the screenshot: a page that renders empty or broken must never reach the user. One screenshot per new page is enough; on Windows, headless Edge works: `msedge --headless=new --screenshot=<png> --window-size=1280,800 <url>` (wrap it in a time limit).
- Theme CSS is cached hard by browsers. When a theme file changes, bump the card's `v` and tell the user to reload with Ctrl+F5.

```js
window.LAB = {
  project: "Название проекта",
  brief: "brief.html",                 // link in the board header; omit until the brief page exists
  rev: 7,
  rounds: [
    {
      id: "r02-structure",
      title: "Главная — структура",
      question: "Что должно быть на первом экране?",
      status: "open",                    // open | decided
      variants: [
        {
          id: "a",
          title: "Сначала продукт",
          axis: "Первый экран — демонстрация продукта",
          rationale: "Посетитель уже знает категорию, ему нужно увидеть интерфейс.",
          tradeoffs: "Ценностное предложение уходит на второй экран.",
          file: "r02-structure/a.html",
          v: 1,
          status: "ready",               // planned | building | ready | chosen | rejected
          note: ""                       // critic's client line
        }
      ]
    }
  ]
};
```

## Template registry

Shared across projects: `index.html` (gallery), `registry.js` (`window.TEMPLATES`), `variables.js`, `kits/`, `systems/`, `layouts/`, `screens/`, `thumbs/`, `tools/`. Format of an entry — its `README.md`. Types: `kit` (themeable page, or a design system `system-<slug>` with `fidelity: "дизайн-система"`), `theme` (token file for a kit), `module` (one block of a kit, shown via `?only=<data-module>`), `layout` (lo-fi structure, or a hi-fi screen on a design system with `kit: "system-<slug>"`); every entry has `product` (what it was made for, e.g. «CRM»).

**Before a round** (R2, R3, R4): `Grep` `registry.js` for the product, the screen and the brief's tags. If there are matches, put them on the board first as a round «Из библиотеки» — the cards' `file` can point at the registry via a relative path or a copy into `lab/` — and ask whether one of them is close enough. Only the gaps get new explorers. Say in one line what was reused.

**After a decided round**, save its variants — chosen and rejected, they are both useful. One command, run from the registry folder:

```
node tools/add-round.mjs "<project>/dev/design/lab" <round> --product <Продукт> [--tags a,b] [--kit <slug>] [--system <slug>] [--test]
```

Run it with `--dry-run` first and read the plan. The script takes titles, rationale, tradeoffs, critic notes and chosen/rejected from `manifest.js`; detects each variant's kind (theme on a skeleton → `kits/<slug>/`; a screen linking `../system/` → copies the system to `systems/<slug>/` and rewrites the links into `screens/`; anything else → `layouts/`); merges with entries saved earlier (same id, or the same file content from the same round) instead of duplicating; then makes thumbnails and rebuilds `variables.js` for every kit and system. `WARN` lines name links the copy would break — fix them by hand.
Still by hand: `module` entries (one per `data-module` block of a new kit) and better `tags` for the gallery filters. Tell the user in one line: «сохранено в шаблоны: N».

## Rounds

Not a waterfall: go back a rung whenever the user's reaction shows the rung below was wrong. Skip rungs that are already decided (an existing product with a design system starts at R3 or R4).

### Sample data — one source
Before the first prototype, write `dev/design/data.md`: the company, counterparties, sums, dates, statuses, totals that must add up across screens. Pass its path to every explorer. An explorer that needs a case the data lacks (e.g. a partially paid invoice) adds it **without breaking the existing totals** and reports the addition; you merge it into `data.md`. Data drift between variants makes the user compare numbers instead of designs.

**Before each round of a new screen, write that screen's data into `data.md` yourself** — every row the prototypes will show (a list's page 1 with numbers, dates, sums, statuses; the totals the tabs or footers claim), checked against the totals already there. Explorers in parallel cannot coordinate: left to fill gaps, each invents different rows (r10: one variant had 14 November invoices, two had 9). Explorers then only add edge cases, as above.

### R0 — Brief, as a page
Copy `.claude/templates/design-brief-page.html` → `lab/brief.html` and fill `lab/brief-data.js` from `.claude/templates/design-brief-data.template.js`: 8–12 questions, each with options the user can click and **a pre-selected working answer**. Mark every answer the user did not give as `assumed: true` — the page shows it as «допущение». Prefer questions the user can answer by pointing ("ближе к Linear или к Notion?"), not by describing. Set `brief` in the manifest so the board links to it.

Then tell the user: open the page, fix what is wrong, press «Скопировать ответы», paste into chat — or write «бриф ок». Two or three short questions in `AskUserQuestion` (without previews) are fine for what blocks the very first round. Write `brief.md` from the answers. **Gate:** the user confirms the brief or says to proceed on the assumptions.

Unknown answers are fine — «не решено, выясняем вариантами» — and the following rounds answer them. If `dev/docs/vision.md` or a market report exists (full kit), take audience, analogues and anti-goals from them instead of asking again.

### R1 — References (optional)
The user named sites — or the brief is too thin to propose directions and the user agreed to look at references first (ask, do not assume). Spawn `design-researcher` per URL in parallel. Append each `index_line` to the library `INDEX.md`.

**Three kinds of research.** *Folder mode* — the user collected screenshots ("посмотри мою папку"): one researcher per folder, the task gives the path and one line of what to look for; no web, the cheapest kind — prefer it whenever the user has screenshots. *Site mode* — the user named a site: one researcher per URL. *Pattern mode* — nobody named a site but the next round needs to know how real products solve a screen or a component ("invoice table on desktop", "bulk actions", "empty state"): one researcher per pattern, the task gives the pattern, the platform and what the project needs from it. **Research costs tokens and time (a run is roughly 150k tokens and 5–10 minutes) — never start it on your own.** By default a round goes without research: the registry and `<library>/` are checked for free (`Grep`), and the explorers give variants anyway. Start a researcher only when (a) the user asks for it («посмотри, как это делают другие», a named site), or (b) you proposed it and the user said yes. Propose it in one line, only when a round is about a screen kind that neither the registry nor `<library>/patterns/` covers and the brief gives no direction: «Перед раундом могу посмотреть, как <шаблон> делают 3–5 продуктов — ~10 минут. Запустить?». A «no» is recorded in `decisions.md` and not asked again for that screen. Its `forks_ru` are candidate axes for the round's variants: use them when planning directions and say which fork each variant takes. A pattern run has no `index_line`; the library entry is `<library>/patterns/<pattern>.md`.

**Show references on the board, not in chat.** The board server serves only `lab/`, so copy each researcher's `screens_ru` files into `lab/<round>-refs/` (e.g. `r01-refs/attio-record-page.png`) and add a round «Референсы» to the manifest: one card per screenshot, `file` = `ref.html?img=<round>-refs/<file>.png` (copy `.claude/templates/design-ref-view.html` to `lab/ref.html` once — a bare PNG in the card frame shows only its top-left corner), `title` = `title_ru` with the domain, `rationale` = `caption_ru`, `axis` = the domain; the takeaways go into the round's `question` as one line per site. Screenshot the board before sending the link. Then ask what attracts and what repels — the *dislikes* are the most valuable input. Record reactions in `decisions.md`.

### R2 — Directions on the board
Registry check first. Then write the planned directions straight into the manifest as cards with `status: "planned"`: title, axis, one sentence of rationale, the cost. Tell the user in 3–4 lines what is planned and that the cards are on the board, and start the explorers in the same turn unless the user must choose between more than four directions — then let them cross out first. The lo-fi prototypes themselves are the plan preview: they are cheap and they are what the user can actually judge.

### R3 — Structure (lo-fi)
Spawn one `design-explorer` per direction, `fidelity: lofi`, in parallel, in the background. Set their cards to `building`. As each returns: card → `ready`, bump `rev`, tell the user in one line that it is on the board. Do not wait for all of them before the user can look. Lo-fi rounds usually do not need the critic — spawn it only if the variants look alike.

### R4 — Style, through tokens
Style is a set of tokens on one approved structure, not ten different pages:
1. **Skeleton.** One `design-explorer` turns the approved lo-fi into `r03-style/page.html`: the same DOM and content, every visual value through role-named CSS custom properties, defaults in its own `:root`, the theme loaded from `?theme=<id>` as `themes/<id>.css` after the page styles, `data-module` on each block, a dev theme switcher hidden in iframes and under `?embed=1`. It writes `themes/_contract.md` — every token, its role, its default. You write `themes/index.js`.
2. **Themes.** One `design-explorer` per theme, in parallel; each writes only `themes/<id>.css` — tokens on `:root`, optional Google Fonts `@import`, nothing else. Before spawning, describe each direction in words on the board (planned cards); the user can strike some out.
3. **Critic** as soon as the themes are ready, concurrently with the user looking; client lines go into the cards' `note`.

**When the critic is mandatory:** every style round (R4), and the first screen built on the design system (first R6 round). Optional elsewhere — spawn it when variants look alike, when a variant is going to become a basis for other screens, or when the user asks. When you skip it on a hi-fi round, say so in one line.
4. **Skeleton fixes** the critic finds that are common to all themes go into `page.html` once (one explorer), not into ten themes.

A theme can be mixed cheaply («шрифт из 04, цвета из 06») — it is only tokens.

### R5 — Convergence
After structure and style are approved: `design-system-builder`. Show the gallery (`system/index.html`) and the rebuilt screen as a round on the board next to the chosen variant, with `normalisations_ru`. Each `decisions[]` fork it returns becomes a `component` round. **A component fork is built by ONE explorer that writes all its variants** (`a.html`, `b.html`, `c.html` with identical content, only the fork differs) — cheaper, and the variants stay strictly comparable. Structure and style rounds keep one explorer per variant.

**Gate:** user approves `DESIGN.md` + gallery. From here on, prototypes import `system/tokens.css` and raw values in design code are a defect.

### R6 — Remaining screens
Each new screen: explorers build from gallery components.

**Patterns flow back into the system.** Explorers report page-level patterns they had to invent (`new_patterns` in their reply: filter chips, pagination, a toolbar…). Append each to `dev/design/system-queue.md` (pattern, which variant, file, whether that variant was chosen). Patterns of a **chosen** variant go into the system: re-launch `design-system-builder` with the queue once a screen is decided (or when 3+ items wait), then clear the done items. Patterns of rejected variants stay in the queue as notes. Still in variants wherever the layout is a real question; a screen that follows an approved pattern needs none. Hand-off to implementation (full kit: `frontend-developer`, whose `ui-patterns-*.md` cites `DESIGN.md`).

## Asking the user

- One round — one question. Options are the variant letters plus **«смешать»** and **«ни один»**; free text is always available.
- State your recommendation and the critic's, in one line each, *after* the options — do not lead with it.
- **«Смешать»** → ask what from which; `SendMessage` to the explorer of the base variant (it keeps its context); the result is a new card (`a2`) next to the originals so before/after is visible.
- **«Ни один»** → do not regenerate blindly. Ask what is wrong *along the axes* ("слишком плотно или слишком пусто?", "слишком строго или слишком игриво?"). Two misses in a row on the same rung → the rung below was wrong: go back (style misses → revisit structure or brief).
- A vague reaction ("что-то не то") → offer two contrasting micro-variants of the suspected property; a pair is easier to judge than a description.
- After every answer, before anything else: append to `decisions.md`, set `chosen` / `rejected` on the cards, set the round to `decided`, bump `rev`, save the round to the template registry.
- A remark about **how the agents work** (not about the design) → change the behaviour in this session, propose the permanent rule, and edit the agent files only after the user agrees.

`decisions.md` entry:

```markdown
## r03-style — 2026-11-14
Показано: A «Строгий редакционный», B «Тёплый продуктовый», C «Плотный технический»
Выбрано: B, с типографикой из A
Отклонено: C — «слишком похоже на админку»
Следствие: не предлагать моноширинные акценты и плотные таблицы на маркетинговых страницах
```

The «Следствие» line is the point of the log: it is what you pass to agents so a rejected idea is never proposed twice.

## Delegation — lines you owe every design agent

- Round id, fidelity, the exact output path, the lab URL of that file.
- The direction: axis + this variant's position on it + what the sibling variants are doing (so it stays distinct).
- Slices, not files: the relevant brief paragraphs and the «Следствие» lines from `decisions.md`.
- For `hifi`: the approved structure file or the skeleton + contract. For anything after R5: `dev/design/DESIGN.md` and `system/tokens.css`.
- Registry or library entries worth consulting, by path — not "look in the library".
- When several agents run in parallel: remind them the Playwright browser is shared (their own page — see the agents' «Browser» section).

Revision of an existing variant → `SendMessage` to the same explorer, not a new spawn.

## Choosing the axis

Variants must differ in one thing the user can name, or the choice is noise. Typical axes — structure: what leads the first screen · navigation model · density · one long page vs steps. Style: tone (strict ↔ playful) · colour temperature and amount · type character · surface (flat ↔ layered). Include one safe position and one bold one; three safe variants teach nothing.

## Language

Everything the user reads — questions, board cards, the brief page, `brief.md`, `decisions.md`, registry names and summaries — Russian. Delegation prompts and agent replies — English.
