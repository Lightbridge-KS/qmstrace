---
summary: E6, the dogfooding experiment — qmstrace traced by its own ledger, and two fresh agents run against it. Run A tests PRD success criterion 5 (from the tool's own output to a proposed pull request) on a real repo whose docs are lens-written; run B, after a human-approved baseline, tests criterion 6. The test bed as pinned, the protocol, the verbatim brief, the measures and the seeded mutation sample fixed before each run, the caveats, and the results.
read_when:
  - about to run, repeat or extend run A or run B of E6
  - judging whether PRD success criteria 5 and 6 are met by the engine
  - changing the stanza, the skill, the Markdown extractor or a finding that a traced engine repo would meet
---

# E6 — dogfooding: qmstrace traced by its own ledger

Terms follow [`CONTEXT.md`](../../CONTEXT.md). The protocol follows the
[beacon experiments](beacon-authoring-experiment.md) E1–E4, and differs where it says so.

**Status: measures for run A fixed, and approved at STOP 4 (2026-09-28); not run.** Run B's measures are fixed in a later commit,
before it runs.

## What is being tested

Two PRD success criteria that the throwaway stand-in passed and the engine has not yet been
measured against:

- **Criterion 5 (run A).** An agent given only the built-in help and the status view finds a
  gap and proposes the fix as a pull request, with no other instruction.
- **Criterion 6 (run B).** An agent given an ordinary request that would change frozen
  requirements stops before editing and hands over the impact set; once the change request is
  accepted, it builds under it with every changed and added item cited.

Run A also tests what the beacon bed could not:

- **Lens-style docs.** The design docs here were written with the architecture lens skills:
  tables, Mermaid, numbered and nested headings, fenced examples. M9 made the Markdown
  extractor read them; no agent has yet declared items inside them.
- **Scale.** 26 modules and 400 test cases, against beacon's 9 modules and 62 test cases.
- **An existing codebase.** Nothing is greenfield. Requirements are written after the code, so
  the order of work means something different (see *Caveats*).

The question is the same as in E1: does the workflow yield traceability that is **complete,
honest and cheap**, from an agent that knows only what the repo gives it?

## The test bed

`<workspace>` is the folder that holds `qmstrace` and its ledger side by side.

| Part | Role | Pinned at |
|---|---|---|
| `qmstrace` | The product repo, traced as project `QMT`. Run A is launched here, at this path — a clone beside the ledger would read the real checkout as its sibling | `main` at launch — `02caed1`, the merge of #23, unless STOP 5 records otherwise |
| `qmstrace-ledger` | The project side: the trace schema, agreement clauses AGR-1…15 distilled from the PRD's goals and constraints, the change-request register (empty). Read-only for the agent | `a3faeab`; the schema's digest is `sha256:2c2b82ac79917b655e8c7296f01370e27e0b5c6279dbf55b9e081608ddef28b4` |
| the tool | `qmstrace` on the agent's `PATH`, installed from a wheel built at `02caed1` (the M9c merge). Every judgement below uses this tool, never the repo's own edited source | wheel sha256 `d4e1dab1d9dd0cd67081736596f3a8342a1b5b43a3dee5803c7c43b828552365` — every build reports 0.1.0, so the hash is the identity |
| `pr-drafts/` | Where the agent writes the pull request's text and its feedback. Created empty before launch | — |

The setup is [#19](https://github.com/Lightbridge-KS/qmstrace/pull/19) and
[#23](https://github.com/Lightbridge-KS/qmstrace/pull/23): `qmstrace.toml` with the verified
schema copy, the stanza in `AGENTS.md`, the skill copy at `.agents/skills/qmstrace/SKILL.md`
linked from `.claude/skills/qmstrace` so Claude Code lists it, and the meta-tests moved to
their own level folder. Design elements may be declared in
`docs/design/*.md` and in `docs/structure/*.md`, where the blueprint maps the code one module
per line.

**Starting state**, with the pinned tool beside the ledger: 0 requirements, 0 design elements,
26 components, 400 test cases; **0 violations and 26 gaps, all G06** (a module implements no
design element); `check --strict` exits 1.

The chain the schema requires, rules G01–G06; a test that verifies nothing is not a gap:

```
origin clause ◀─Origin── requirement ◀─Satisfies── design element ◀─Implements── component
  (AGR-N)                    ▲   G01                    ▲  G03, G05                 G06
                             └── verifies ── test case ─┘  G02 (Verify-by: test), G04
```

## Protocol

As in E1–E4, with these differences:

- **The teammate is a fresh agent, never a fork**, launched in-process by a driver session
  that is itself fresh and on `main`. It is not told what is measured.
- **The listing is what a real Claude Code session in this repo shows**
  ([appendix](#appendix--the-skill-listing)): the repo's own skill `qmstrace`, found through
  `.claude/skills/qmstrace`, and the coding plugin set of `agent-stuff` at `517cb11`. A
  headless session started in a clone of the launch commit quoted its listing lines verbatim
  (2026-09-28), and the appendix copies them. 18 of the coding skills carry their own
  descriptions; `extensibility-architecture` shows none (its description is a folded YAML
  block); `improve-codebase-architecture` is not listed (`disable-model-invocation`).
  **`qmstrace` is listed as a bare name** — approved at STOP 4 — because the session showed it that way. The cause
  is unknown — its description is one plain line. Listing it with its description would match
  a lighter setup instead of this one. Whether the agent reads the skill is measured
  (E6-A-10).
- **The driver opens pull requests.** The agent commits on a branch and writes the pull
  request's title and body to a file. The driver pushes the branch and opens a draft pull
  request with that text verbatim; the developer's review of it is a measure.
- **Every claim is re-derived by the driver** with the pinned tool: gate results beside the
  ledger and from a clone outside `<workspace>`, mutation flips, AST equality, the Git log,
  the ledger's status.

### The brief, verbatim

Sent as one message. `<workspace>` is replaced by its absolute path, and `<the skill listing>`
by the appendix verbatim, with `~` written out as the home folder.

```text
You are a coding agent. A developer has opened a session for you in this repository:

    <workspace>/qmstrace

Treat that folder as your working directory for everything (use absolute paths or `cd` into it in each command). Start by reading its `AGENTS.md` — a session launched there would have loaded it for you — and follow it.

Skills available in this session (load one by reading its file when its description applies):

<the skill listing>

Boundaries: work only inside `qmstrace`. Outside it you may read `<workspace>/qmstrace-ledger`, run the `qmstrace` command on your PATH, and write the two files in `<workspace>/pr-drafts/` named below. Do not read or write anything else outside the repo. Do not push and do not use `gh`: the developer opens the pull request. Dependencies are installed — use `uv run`; avoid adding packages.

## The developer's request

"qmstrace now traces this repo. Its ledger is next door at ../qmstrace-ledger and belongs to the project side — read it, don't change it. Get this repo through qmstrace's gate and propose the work as a pull request: commit on a branch, and write the pull request's title and body to <workspace>/pr-drafts/qmstrace.md. I'll open it.

When you are done, reply in under 40 lines: the branch and its last commit, the final line of `qmstrace check --strict`, and anything you left undone and why. Put blunt feedback — anything in AGENTS.md, the skill or the tool's output that was unclear, that you had to guess at, or that got in your way — in <workspace>/pr-drafts/qmstrace-feedback.md, and don't commit it."
```

**The brief names the gate and asks for a pull request** — approved at STOP 4. Criterion 5 as written says the
agent does this *with no other instruction* than the help and the status view. This brief is
the developer's ordinary ask — "get it through the gate, propose it" — and leaves how to find
the work to the tool. The stricter reading would be *"qmstrace now traces this repo; take a
look"*, measuring whether the agent volunteers a pull request at all. That is a different
question — initiative, not the tool's steering — and it does not exercise the full trace.

## Run A — measures

Fixed before the run.

| # | Measure | How it is read |
|---|---|---|
| E6-A-1 | The work found from the tool | Its first commands, and where its work list came from: `status` / `check` / `--help`, or reading `src/` for how the checks work. Transcript and its reply |
| E6-A-2 | The gate | Final `qmstrace check --strict`, pinned tool: **exit 0, 0 violations, 0 gaps** beside the ledger; the same from a clone outside `<workspace>`, where the agreement and change requests read NOT VERIFIED. A gap left open counts only if the pull request's text names it and says why |
| E6-A-3 | Proposed as a pull request | A branch with the work in commits; `pr-drafts/qmstrace.md` holds a title and a body that a reviewer can act on. Every factual claim in it — counts, commands, results — re-derived by the driver |
| E6-A-4 | Requirement quality | One checkable statement each; `Category` fits; each `Origin` cites an AGR clause that actually says it; the requirements describe the tool as built — nothing the code does not do. A built behaviour that no clause asks for is raised as a question, not given a loose origin |
| E6-A-5 | Marker honesty — `verifies` | The seeded mutation sample below: every sampled requirement's verdict flips to fail when the source is broken |
| E6-A-6 | Marker honesty — `Implements` | Five seeded modules read against every design element each claims: is the claim true of the code? |
| E6-A-7 | Signs of a thin trace | Modules per design element (largest, median); a design element standing for the whole package; `Verify-by: inspection` or `analysis` used where a test exists or could — each one read; any `Status: withdrawn`; any `ignore` or scan path narrowed |
| E6-A-8 | Rich Markdown held | `check` reports no V16 and no stray; every heading added reads as an item; no fenced example edited (the D8 requirement example, the schema and configuration examples); no settled decision reworded; no existing heading renamed, so anchors stay |
| E6-A-9 | Nothing else touched | `src/` equal to the launch commit by AST apart from module docstrings; in `tests/`, no existing test body changed — only `verifies` decorators and new tests; `qmstrace.toml`, `pyproject.toml`, `.agents/skills/qmstrace/`, `.claude/skills/qmstrace` and the stanza unchanged; the ledger's HEAD and working tree unchanged; `just dry` passes. Any other change is listed and read |
| E6-A-10 | What it read | Whether it read the skill — loaded by name or read from `.agents/skills/qmstrace/SKILL.md` — and before its first marker; which listed skills it loaded, and whether the result follows them. Transcript |
| E6-A-11 | Order of work | Git log: top-down — requirements, design elements, `Implements`, `verifies` — or back-filled from the gap list; commit size |
| E6-A-12 | Ceremony and typed facts | No cover page, revision table, approval block, typed date, verdict or test count in repo memory; a hash or count in the pull request's text is checked against the repo |
| E6-A-13 | Review burden | What the developer corrects in the review, and how long the review takes |
| E6-A-14 | Friction | `pr-drafts/qmstrace-feedback.md`; each testable point confirmed or refuted by the driver |

### The seeded mutation sample (E6-A-5, E6-A-6)

The sample is drawn by a fixed seed after the run, so the driver cannot pick the items that
hold.

**Seed `29110`; six requirements; five modules** — approved at STOP 4.

- **Requirements.** The population is every requirement with `Verify-by: test` and no
  `Status: withdrawn` at the agent's last commit, sorted by ID. The sample is
  `random.Random(29110).sample(population, k=min(6, len(population)))`, on Python 3.13.
- **Modules.** The 26 components cannot change (E6-A-9), so their sample is drawn now:
  sorted by path, `random.Random(29110).sample(components, k=5)` on Python 3.13.2 gives
  `infra/git.py`, `core/baselines.py`, `infra/files.py`, `core/setup.py` and
  `workspace.py`, under `src/qmstrace/`.

For each sampled requirement, in a clone outside `<workspace>`, with
`PYTHONDONTWRITEBYTECODE=1` so no stale bytecode survives between runs:

1. **Break it from its text alone.** Before reading which tests carry its marker, write the
   smallest change to `src/` that makes the requirement's statement false. No test is edited.
   The patch is kept.
2. **Run.** `uv run pytest --junitxml=<report>`, then `qmstrace results <report>` with the
   pinned tool. The requirement's verdict must read *fail*.
3. **Restore.** The verdict reads *pass* again.

A verdict that does not flip is read before it is scored. Either the tagged tests do not
exercise the statement — a decorative marker, the agent's finding — or the break missed the
statement — the driver's error, rewritten and said so.

## Pre-launch — STOP 5

- The global tool is the pinned wheel: every installed package file matches the wheel's
  `RECORD`.
- `qmstrace` is on `main` at the launch commit with a clean tree; `git branch -a` shows no
  `experiment/` branch — checked again immediately before launch. Until run A ends, the
  working copy is updated only with `git pull origin main`, never a bare `git fetch`; a ref
  that appears anyway is removed with `git branch -dr origin/experiment/e6-measures`.
  Background fetches bring it back: on 2026-09-28 the ref appeared in the working copy from
  a `fetch` nobody ran in this checkout by hand, most likely the desktop app's Git
  integration. **The gap is closed for the run** — approved at STOP 4: a negative fetch
  refspec keeps any fetch from storing the ref (checked on a throwaway repo). Set at STOP 5
  with `git config --add remote.origin.fetch '^refs/heads/experiment/*'`; removed after run A
  with `git config --unset remote.origin.fetch '^\^refs/heads/experiment/\*$'`.
- The ledger is at `a3faeab` with a clean tree.
- `<workspace>/pr-drafts/` exists and is empty.
- The starting state above is reproduced with the pinned tool.
- The two memory entries that give the run away — *qmstrace test bed* and *Background fetch
  leaks hidden branches* — are parked outside the memory folder and their index lines removed
  (decided at STOP 4); both are restored after run A.
- The product repo holds no E6 material: its gitignored `_playground/` — where earlier session
  notes name this run — is parked at `<workspace>/_tests/qmstrace-e6/parked-playground/` until
  run A ends, and E6's driver material lives in `<workspace>/_tests/qmstrace-e6/`.
- The brief sent is `<workspace>/_tests/qmstrace-e6/run-a/brief.txt`, assembled from this
  document; its `assemble.py --check` proves the round trip.
- With the developer's go, `git gc --prune=now` drops the objects the leaked fetches left
  unreferenced in the working copy's `.git`.

## Caveats

- **The repo describes its own experiments.** `AGENTS.md` has an *Experiments* section, the
  PRD states criteria 5 and 6, and `docs/tests/` holds E1–E4. The tracker on `main` is
  neutral and this document is on an unmerged branch, but the agent can tell that agents are
  tested here.
- **The agent has the tool's full source.** It can read how each finding is computed, and it
  could change the tool to pass its own gate. The pinned tool judges, and E6-A-9 compares
  `src/` by AST.
- **It traces existing code.** Requirements cannot precede the code they describe; order of
  work (E6-A-11) reads as top-down against back-filled from the gap list, not as
  requirements-before-code.
- **Inherited context.** An in-process teammate inherits the developer's user-level
  instructions, the project's memory index and the session's Git status. That is faithful to
  this developer's setup and silent about anyone else's.
- **Fidelity.** A spawned teammate does not auto-load `AGENTS.md` or skills, so the brief tells
  it to. A session launched by a person in the folder should confirm any finding that matters.
- **The measures branch can surface.** A background fetch stores `origin/experiment/e6-measures`
  in the working copy unless the refspec above is set; the agent would then see a branch name,
  and could read this document from it. Objects from the fetches before the refspec stay in
  `.git` unreferenced until garbage collection. The transcript shows whether it looked.
- **Siblings are visible.** Other folders in `<workspace>` can be listed from `..`, among them
  the beacon test bed of E1–E4 with its stand-in. The brief's boundary forbids reading them;
  the transcript shows whether it held.
- **One run, one strong model.** Not a rate; a first observation.

## Run B — criterion 6

After run A's pull request merges and the developer cuts `baseline/requirements/1` (STOP 7).
The request, its answer key from `qmstrace impact` at the tag, and measures E6-B-1…, modelled
on E3-1…8, are fixed in a second commit on this branch before it runs.

## Results

Not run yet.

## Appendix — the skill listing

As a real Claude Code session in this repo lists these skills — the repo's own `qmstrace` and
the coding plugin set of `agent-stuff` at `517cb11` — in the brief exactly as below, sorted
by name. A description is shown where the session showed one; each is the skill's own, from
its `SKILL.md`. `<workspace>` and `~` are written out when the brief is sent.

```text
- `agentic-architecture` — Explain an existing agentic system — an AI agent as the central "CPU" with its organs (loop, memory, tools, skills, MCP, subagents, hooks) — or design one from requirements. Use on name or near-match.
  File: ~/.claude/skills/agentic-architecture/SKILL.md
- `ax-interface` — The agent-experience ("AX") lens for any interface an AI agent drives — CLI, MCP server, REST API, or SDK. Audit an existing surface against the AX principles, or apply them while designing a new one. Use on name or near-match ("AX analysis", "agent-friendly interface"). For a whole-surface doc across all audiences, use `surface-architecture` instead.
  File: ~/.claude/skills/ax-interface/SKILL.md
- `c4-architect` — Design a system as C4 diagrams (C1–C3) through phase-gated Q&A — ASCII inline, Mermaid to disk. Use when the user wants to design or model a system through dialogue, or mentions C4. For compiling already-settled inputs without elicitation, use `system-architecture` instead.
  File: ~/.claude/skills/c4-architect/SKILL.md
- `clean-architecture` — How I apply Clean Architecture + DDD — pragmatic, right-sized by complexity tier, reconciled with deep modules. Use when designing, reviewing, or refactoring a codebase's architecture or layering, deciding how much architecture a project needs, or whenever Clean Architecture / DDD / SOLID comes up.
  File: ~/.claude/skills/clean-architecture/SKILL.md
- `codebase-blueprint` — Reconcile settled design docs with each other and the chosen framework, then compile the object model that satisfies all of them — prose rules become machine-checked invariants. Use when design is settled and you are about to build, or on name / near-match.
  File: ~/.claude/skills/codebase-blueprint/SKILL.md
- `codebase-design` — Shared vocabulary for designing deep modules — terms and principles, no document produced. Use when designing or improving a module's interface, placing a seam, or making code testable or AI-navigable; also loaded by other skills needing this vocabulary. For the pre-code object-model document, use `codebase-blueprint`.
  File: ~/.claude/skills/codebase-design/SKILL.md
- `commit-push-pr` — Git workflow: commit, push, and create/update a draft PR. If a PR exists for the current branch, update its body. Trigger: 'commit push pr' or /commit-push-pr.
  File: ~/.claude/skills/commit-push-pr/SKILL.md
- `data-architecture` — Explain an existing codebase's data architecture — where data rests (stores, schema) and how it moves (dataflow, lineage) — or design one from requirements. One Markdown doc with Mermaid diagrams. Use on name or near-match.
  File: ~/.claude/skills/data-architecture/SKILL.md
- `design-md` — Author, extract, lint and export a repo's root DESIGN.md — the visual identity spec (Google design.md format: YAML design tokens + prose rationale) that any coding agent follows when building UI. Use when a repo needs a design system agents can follow across harnesses, when asked for design tokens, brand tokens, a theme file or "a DESIGN.md", before building or restyling UI in a repo that has one, or when a brand skill's identity must land in a codebase. Not for system design docs (`docs/design/`).
  File: ~/.claude/skills/design-md/SKILL.md
- `domain-modeling` — Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
  File: ~/.claude/skills/domain-modeling/SKILL.md
- `extensibility-architecture`
  File: ~/.claude/skills/extensibility-architecture/SKILL.md
- `grill-with-docs` — A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
  File: ~/.claude/skills/grill-with-docs/SKILL.md
- `harness-design` — Decide how much agent harness to own — off-the-shelf, middleware on one, a custom loop, or an explicit graph — from the task's distribution distance and its need for control; then shape what stays yours (instructions, skills, environment, evals) and the flywheel that improves it. Use when designing or reviewing an agent harness, choosing between a hand-rolled loop, a framework and a hosted harness, deciding whether something should be a tool or a skill, setting up evals for an agent, or when a harness has grown while models improved. Also on harness engineering, file-system agent, agents-as-files, cognitive architecture, Harbor, Eve, Antigravity, Deep Agents. For mapping the organs of an existing agent, use `agentic-architecture`; for the UI it emits, `generative-ui`.
  File: ~/.claude/skills/harness-design/SKILL.md
- `qmstrace`
  File: <workspace>/qmstrace/.claude/skills/qmstrace/SKILL.md
- `security-architecture` — Explain an existing system's security architecture — what is worth protecting, where trust changes hands, what crosses each boundary uninvited, and which control (located in code) stops it — or design one from requirements. One Markdown threat-model doc with Mermaid diagrams. Use on name or near-match (threat model / STRIDE / trust boundary / attack surface). For finding vulnerabilities in code, use `/security-review` (a diff) or the `claude-security` plugin (a repo) instead; this lens tells them where to look.
  File: ~/.claude/skills/security-architecture/SKILL.md
- `surface-architecture` — Explain or design a codebase's user-facing surface — UX/DX/API from outside the boundary, for end user, developer, or agent. One Markdown doc with Mermaid diagrams. Use on name or near-match.
  File: ~/.claude/skills/surface-architecture/SKILL.md
- `switch-pull-prune` — Git workflow: after a PR merges, switch to the base branch, pull, and prune the merged branch. Trigger: 'I've merged the PR' or /switch-pull-prune.
  File: ~/.claude/skills/switch-pull-prune/SKILL.md
- `system-architecture` — Explain an existing codebase's system architecture, or design one from a PRD or rough ideas — either way one C4-style Markdown doc with Mermaid diagrams. Use on name or near-match.
  File: ~/.claude/skills/system-architecture/SKILL.md
- `testability-architecture` — Explain how an existing system proves it works — the claims it must keep, which test level proves each, where seams let a test swap real for double, which gate runs it, and who judges (developer, CI, AI agent, end user) — or design that test architecture from requirements. One Markdown doc with Mermaid diagrams; architecture, not a runbook. Use on name or near-match (test strategy / test pyramid / test levels / test doubles / "how should we test this?").
  File: ~/.claude/skills/testability-architecture/SKILL.md
- `yolo-ship` — Autonomous git workflow for low-risk work: commit → push → PR → watch CI → fix if red → merge when green → switch-pull-prune. OPT-IN ONLY: invoke only when the user explicitly says 'yolo ship' or /yolo-ship in the current turn — never self-select, never chain from another task.
  File: ~/.claude/skills/yolo-ship/SKILL.md
```
