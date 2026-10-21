---
summary: ADR-0006 — a new product repo's starter declares the item types of its language, chosen from the build files at or just below the repo root (.NET solution or project file → C#, pyproject.toml → Python, neither → Python); init names the starter and why; a repo holding both is refused, and --language settles it. Amends the setup contract's "creates a repo-owned starter" and requirement REQ-QMT-12 (CR-005).
read_when:
  - changing which starter `init` writes, or adding a language to it
  - adding or moving a packaged starter asset
  - deciding whether setup may read a repo's own build files, or whether an option may override what a folder's contents say
---

# ADR-0006 — The starter a repo's shape chooses

- **Status:** accepted, 2026-10-21
- **Amends:** [surface architecture](../design/surface-architecture.md) *Setup contract — M6*
  ("creates a repo-owned starter", and its rejection of flags that name what a folder's contents
  already say); [codebase blueprint](../structure/codebase-blueprint.md) — the asset inventory
  and DSN-QMT-11; requirement REQ-QMT-12, under CR-005
- **Decided by:** the developer, 2026-10-21 (qmstrace issue #38)

## Context

`init` wrote one product-repo starter, whose `[items]` declared Python item types: components
read by `python-module` from `src/**/*.py`, automated tests read by `pytest` from
`tests/**/test_*.py`. In a C# repo that starter scans no file — the repo reads as traced while
declaring nothing, and every coverage rule about components and automated tests is unmet until
someone rewrites `[items]`.

This was foreseen when C# reading was accepted: ADR-0004's consequences record that `init` has
no C# starter yet, and CR-003 put it outside its scope. The first real project is a C# repo, so
every new repo of that project paid for the deferral by hand, and the manual's C# how-to carried
a caveat telling readers to edit `[items]` and delete a `pytest.ini` they did not want — which
this project treats as a design finding, not a documentation task.

## Decision

- **The repo's build files choose the language** whose item types a new configuration declares.
  A .NET solution or project file means C#; a `pyproject.toml` means Python; neither means
  Python, as every starter did before.

  | Language | Build files, as patterns relative to the repo root |
  |---|---|
  | C# | `*.sln`, `*.slnx`, `*.csproj`, `*/*.csproj`, `src/*/*.csproj` |
  | Python | `pyproject.toml` |

  The .NET patterns reach a solution or project file at the root, a single-project repo, and the
  conventional `src/Project/`, and stop there. A starter is a starting point, not a survey of
  the tree, and a reach nobody can state is a reach nobody can predict.

- **A repo holding the build files of both is refused** (exit 2), naming the files it found,
  with `--language` as the next move. Which language holds a mixed repo's components is a real
  question about that project, and this engine does not answer such a question by guessing.

- **`--language python|csharp`** settles it, and overrides detection anywhere. It is refused when
  a configuration already exists, as `--subject` and `--key` are, and in a ledger, which holds
  the project's documents rather than code.

- **`init` names the starter it chose and why**, as its first line — `starter: csharp
  (App.csproj)`, `starter: python (the default; no build file names a language)` — so the choice
  is auditable from the run that made it, not reconstructed from the file it wrote.

- **One starter asset, with a swappable tail.** `assets/starter.toml` holds the project schema,
  the subject and the two document item types, all language-neutral; `assets/items-python.toml`
  and `assets/items-csharp.toml` hold only `[items.component]` and `[items.automated_test]`.
  `init` joins the starter and one fragment, then substitutes the subject and key as before.

- **No `ignore` list in the C# fragment.** Generated source that a build commits — EF Core
  migrations, designer files — is a component with nothing to implement, and the fragment says
  in a comment that such paths belong in `ignore`. Which paths those are is a fact about a
  project, not about C#, and setup supplies a reviewable starting point, not project policy.
  (`ignore = ["**/__init__.py"]` in the Python fragment is a fact about the language.)

## Consequences

- REQ-QMT-12 gains the starter choice, under CR-005; DSN-QMT-11 gains it beside its ledger
  choice. No new requirement: choosing the starter is a refinement of "a product repo is set up
  by one command".
- Setup now reads files the repo owns and qmstrace does not — the first time it looks at
  anything but its own markers, `.claude/` and the pytest settings it edits. It reads their
  names only, never their contents, and the reach is the table above.
- The pytest marker needed no second rule: it was already registered only where an item type
  uses the `pytest` extractor, so a C# starter writes no `pytest.ini` on its own.
- A repo whose language qmstrace cannot name still gets the Python starter, so nothing that
  worked before changes.
- **Docs that follow:** the setup contract, the blueprint's asset inventory and DSN-QMT-11, the
  scenario catalogue, the C# how-to (its caveat deleted), the `init` reference page.

## Rejected alternatives

- **Two complete starters, one per language.** One file per language reads cleanly as a
  reviewable document and keeps the choice a single line, but about eighty-five lines of schema
  — link types, the coverage rules G01–G07, the categories — would exist twice, and the next
  schema change would have to be made in both or they drift.
- **Detection alone, with no option.** Consistent with the rejection of an `init --ledger` flag
  in the setup contract, where the folder's contents decide. It fails on the case that made the
  option worth having: a ledger is recognised by `qmstrace.schema.toml`, a file qmstrace itself
  owns and that cannot be ambiguous, while two languages' build files legitimately sit side by
  side, and then there is nothing for detection to decide.
- **An option alone, with no detection.** Honest, and nothing to predict — but it makes the very
  first run on a repo wrong by default, which is the whole of this issue.
- **A tie-break instead of a refusal** — any .NET marker wins, or Python wins. Never blocks, and
  the printed line is the only warning that the configuration may scan the wrong half of the
  repo. A starter that declares the wrong item types is worse than a second command.
- **Walking the tree for `*.csproj`.** Finds a project file at any depth, at the cost of a reach
  nobody can state and a scan of whatever the repo happens to contain. The patterns above are
  what a .NET repo conventionally has.
- **Detecting from file counts** — more `.cs` than `.py`. Guesses on exactly the mixed repo that
  needs a person to decide, and says nothing about why it chose.
