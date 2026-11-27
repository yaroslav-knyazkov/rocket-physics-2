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

- Exact relationship between this repo (core/API) and `fx27` (the driving project): is `fx27` a consumer of the API (separate repo depending on this one), or is it a parallel/sibling piece of work that informs requirements? Needs clarifying with the user during `vision`/`architect`.
- API language/stack not yet decided — v1's stack is unknown to this note; `architect` should ask or check if v1 source is available for reference (not for reuse, just for "what to avoid").
- Scope of "Models" / "Simulations" / "Optimizations" taxonomy should be pulled from v1's LaTeX once the user writes/shares it, not guessed.
