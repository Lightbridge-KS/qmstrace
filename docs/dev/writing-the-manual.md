---
summary: How the user manual in contents/ is written and built — Diátaxis, a TL;DR on every page, reference framed around goldens and fixtures that tests own, the friction rule that turns a caveat into a ux issue, and the Zensical build that Netlify publishes.
read_when:
  - adding or changing a page under contents/, or changing what a command prints
  - finishing a milestone — it ships its manual pages
  - a page seems to need a caveat or a workaround
---

# Writing the user manual

The **user manual** (`contents/`, built by Zensical, published on Netlify at
<https://qmstrace.netlify.app/>) is for the people who use qmstrace. `docs/`, this folder, is the
repo's memory and is never published. Terms follow [`CONTEXT.md`](../../CONTEXT.md).

## Every milestone ships its pages

A milestone's pull request carries the pages for what it built, in the quadrants it touches —
not every milestone needs all four. Writing a page is a usability test of the command: **a page
that has to warn about a caveat is a design finding.** File it as a GitHub issue labelled `ux`
(the feature template) — unless a milestone already owns the gap, in which case the page says
*not built yet* and nothing is filed.

## Four kinds of page (Diátaxis)

| Folder | Kind | Written for | Rule of thumb |
|---|---|---|---|
| `tutorials/` | learning | a newcomer | one guaranteed outcome on the example project; no choices |
| `how-to/` | a goal | someone who knows what they want | steps only; link out for the why |
| `reference/` | facts | someone looking something up | austere; generated or included wherever the code is the source |
| `explanation/` | understanding | someone asking why | the reasons and the rejected alternatives; no steps |

A page that mixes two kinds is split.

## The shape of a page

```markdown
# Title

!!! abstract "TL;DR"

    Three to five lines: what, when, and the one command.
```

Then the body. Zensical has no `tldr` admonition type, so the TL;DR is an `abstract` box with
that title — `tests/test_manual.py` checks every page opens this way. Diagrams are Mermaid
fences. A page reached from nowhere is dead: every page is listed in `nav` in `zensical.toml`.

## Never restate what the tool prints

What qmstrace prints is included, never retyped. `pymdownx.snippets` includes files from
`tests/` only (`base_path`), and a missing file fails the build:

| Include | From | Owned by |
|---|---|---|
| a command's output | `cli/golden/<command>-<case>.txt` | `tests/cli/` |
| a command's help, the exit codes | `cli/golden/help.txt`, `help-<command>.txt` | `tests/cli/test_help.py` |
| the findings table | `manual/findings.md` | `tests/test_manual.py`, from `core/findings.py` |
| a configuration example | `fixtures/mini/**` | the tests that parse the fixture project |

```markdown
``` text
--8<-- "cli/golden/status-service.txt"
```
```

Regenerate after an intended change with `QMSTRACE_REGOLD=1 just test`, and read the diff.
**A changed golden means re-reading the prose around it:** `rg <golden-name> contents/` finds
every page that frames it.

## Build and publish

```sh
just manual         # live preview at http://localhost:8000
just manual-build   # strict build — a broken link, anchor or include fails; part of `just dry`
```

The build runs in an isolated environment (`uv run --isolated --only-group docs`), because
Zensical depends on `click` and the project's environment must not. Netlify builds from
`netlify.toml` — a deploy preview on every pull request, production on each merge to `main` —
and skips a build when nothing the manual reads has changed.

`contents/` is published, so a change to it always goes through a pull request, never straight
to `main`. Nothing project-specific is ever written there: examples come from the fixture
project.
