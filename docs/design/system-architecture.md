---
summary: System architecture of qmstrace at C1–C2 with a first C3 for engine slice 1 — who and what the tool touches (product repos, a ledger repo, Git, test reports, the render machine, people), the three kinds of repository and what flows between them, the package's modules and their one seam that matters (the source tree), and the two key flows.
read_when:
  - deciding where a responsibility lives — the engine, a product repo, the ledger repo, or a system outside
  - adding a module, or a dependency between modules, to the engine
  - explaining the whole system to someone new in one page
---

# qmstrace — System & OOP Architecture

> Source: the PRD, decisions D1–D10, the surface architecture, the slice-1 tracker and four experiments on a test bed · Date: 2026-09-21 · Mode: Design · Type: Application (a command-line tool)
> See also: [Data Architecture](data-architecture.md) · [Surface Architecture](surface-architecture.md) · [Product Requirements](../req/qmstrace-prd.md) · [Slice 1 tracker](../progress/slice-1-product-repo-half.md)

Terms follow [`CONTEXT.md`](../../CONTEXT.md). **✔** marks what an experiment exercised,
**◻** what is planned.

## 1. Overview

qmstrace keeps the state, traceability and audit evidence of a software project's work
products, so that an auditor's questions are answered by query instead of by assembly. It is
**a tool installed into repositories that already exist** — it holds no project data, runs no
server, and owns no evidence: it reads markers where people and agents already write, judges
them, and points at evidence that stays in its home system.

**Type: application** — a single command-line entry point, `qmstrace`, with package data (a
skill, a stanza template) shipped beside the code. Nothing is meant to be imported.

**Stack:** Python 3.13+, `uv`, `typer`; the standard library for TOML, `ast` and globbing;
`defusedxml` for test reports. An in-memory DuckDB arrives with the ledger (slice 2).

## 2. System Context

```mermaid
flowchart LR
    dev(["Developer-manager"])
    agent(["Coding agent"])
    rev(["Reviewers and approvers"])
    aud(["Auditor"])
    subgraph Q["qmstrace — the engine"]
        cli["command line"]
    end
    prod[("Product repos — code, tests, repo memory, markers")]
    led[("Ledger repo — agreement, change requests, trace schema, trace lock")]
    git["Git — tags are baselines"]
    rep["Test runner — reports"]
    rend["Render machine — Word drafts"]
    store["Document store — signed revisions"]
    host["Git host and tracker"]
    dev --> cli
    agent --> cli
    cli --> prod
    cli --> led
    cli --> git
    rep --> cli
    led --> rend
    rend --> store
    rev --> store
    aud --> led
    host -.-> led
```

| Outside the engine | What crosses the boundary | Status |
|---|---|---|
| **Product repos** | The engine reads markers and the trace configuration; `init` writes the configuration and a stanza. It never writes requirements, design or code | ✔ |
| **Ledger repo** | The engine reads the trace schema, the agreement and the change requests; the ledger group writes the trace lock | ✔ import (by the driver of an experiment) |
| **Git** | Tags are baselines; a tree at a revision is a source like any other | ✔ |
| **Test runner** | A report file comes in; verdicts are never typed | ✔ |
| **Render machine** | The engine emits tables as data; a predecessor's machinery turns them into Word drafts. The engine knows nothing about Word | ◻ |
| **Document store** | Reviewers read, edit and sign there. A signature becomes an event with an evidence pointer — how, is open | ◻ |
| **Git host and tracker** | Collectors harvest facts — reviews, merges, states — with the home system's own timestamps | ◻ |

Two launch sites, one per hat: the **product repo**, daily, for the standard's
software-implementation process; the **ledger repo**, occasionally, for its
project-management process (D5).

## 3. High-Level Structure

Three kinds of repository, and what moves between them:

```mermaid
flowchart TD
    subgraph E["qmstrace — engine repo: the tool, no project data"]
        pkg["package + skill + stanza template"]
    end
    subgraph P["Product repos — many per project"]
        mem["repo memory with markers"]
        code["modules and tests with markers"]
        conf["trace configuration — local part + a verified copy of the schema"]
    end
    subgraph L["Ledger repo — one project's record"]
        schema["trace schema"]
        agr["agreement and change requests"]
        lock["trace lock — generated, committed"]
        docs["controlled-document sources"]
    end
    pkg -- "installed into" --> P
    pkg -- "installed into" --> L
    schema -- "generated, verified copy (D9)" --> conf
    P -- "import at a pin (D2)" --> lock
    agr -. "cited by ID: origins, change requests" .-> mem
    lock --> docs
```

| Where | Responsibility |
|---|---|
| **Engine repo** | The tool and what ships with it. Fixtures are a hand-made miniature — never a real project |
| **Product repo** | Requirements, design elements, modules and tests, each declared where it is written, links at the downstream end (D1). Its check is local and fast; what it reads from a sibling is *not pinned* and says so |
| **Ledger repo** | What belongs to the project and to no product repo: the agreement, change requests, the trace schema, the union of all repos at pins, the documents generated from it |

## 4. Components

The engine's package for slice 1. The decisive seam is **the source tree**, not Git: one scan
runs over a working tree, a tree at a baseline tag, or a sibling.

```mermaid
flowchart TD
    cli["cli — wiring only; maps outcomes to exit codes"]
    ws["workspace — Workspace.open(root).assessment()"]
    subgraph core["core — pure, no IO"]
        config["config — parse, validate, merge, provenance"]
        graph["graph — TraceGraph; an illegal link never enters"]
        judge["judge — coverage, baselines, guard, suspects"]
        find["findings — the catalogue: what is wrong, the next move"]
    end
    subgraph extract["extract — IExtractor takes text"]
        md["markdown"]
        py["python module"]
        pt["pytest + the report reader"]
    end
    subgraph infra["infra"]
        tree["ISourceTree — working tree · tree at a revision"]
        igit["IGit — state, reachable tags, files and text at a revision"]
        ext["externals — agreement, change requests, siblings"]
    end
    render["render — functions returning text"]
    cli --> ws
    ws --> config
    ws --> tree
    tree --> igit
    ws --> extract
    ws --> graph
    ws --> judge
    ws --> ext
    judge --> find
    cli --> render
```

`core` imports nothing from `infra` or `extract`. A command is *open → render → exit*; the
assessment is computed once and every renderer reads it.

## 5. OOP & Class Architecture

A sketch — the object model is the blueprint's job (`docs/structure/`).

```mermaid
classDiagram
    class ISourceTree {
        <<abstract>>
        +files() paths
        +read(path) text
        +label
    }
    class WorkingTree
    class GitTree
    class IExtractor {
        <<abstract>>
        +extract(path, text, spec) Extracted
    }
    class IGit {
        <<abstract>>
        +state() RepoState
        +tags_reachable_from_head() tags
        +read_files(rev, paths) texts
    }
    class TraceGraph {
        +build(extraction, schema, siblings, externals)
        +node(id)
        +downstream(ids) Closure
        +upstream(ids) Closure
    }
    class Workspace {
        +open(root)
        +assessment() Assessment
    }
    ISourceTree <|-- WorkingTree
    ISourceTree <|-- GitTree
    GitTree --> IGit
    Workspace --> ISourceTree
    Workspace --> IExtractor
    Workspace --> TraceGraph
```

- **Interfaces only where something really varies**: the tree (two now, a pin in slice 2),
  the extractor (three now, another test framework later), Git (a real one; a scrubbed
  environment in tests). No repository pattern, no composition root — the Modular tier.
- **Judgement is pure functions**, not a class: `coverage`, `resolve_baselines`, `guard`,
  `suspects`. None touches Git or a file.
- **`Closure`** keeps the edge that reached each node, so `thread`, `impact` and suspects are
  three renderers of one traversal.
- **Value objects are frozen dataclasses.** A finding is data — code, file, line, item, what
  is wrong, the next move — and the line an agent reads is one renderer of it.

## 6. Key Flows

### A check in a product repo ✔ (as the stand-in ran it) → ◻ (as the engine will)

```mermaid
sequenceDiagram
    participant A as Agent or developer
    participant C as cli
    participant W as workspace
    participant T as source tree
    participant X as extractors
    participant J as core: graph and judge
    A->>C: qmstrace check
    C->>W: open(root).assessment()
    W->>T: files and text — working tree
    W->>X: extract(path, text, spec)
    X-->>W: items with digests, raw links, findings
    W->>T: the same, at the governing baseline tag
    W->>J: build the graph, judge it
    J-->>W: violations, gaps, suspects, notices
    W-->>C: Assessment
    C-->>A: findings — what is wrong, the next move · exit 0, 1 or 2
```

### A project judged as a whole ◻ (slice 2; run once by hand in the fourth experiment)

```mermaid
sequenceDiagram
    participant M as Project side
    participant L as qmstrace ledger import
    participant P as Product repos
    participant K as trace lock
    M->>L: import gateway@tag agent@tag
    L->>P: read each repo at its pin — never a working tree
    L->>L: union · authored IDs unique · derived IDs qualified by repo
    L->>L: verify each repo's copy of the schema; judge across repos
    L->>K: write — sorted, byte-identical on a second run
    K-->>M: the diff a reviewer reads
```

## 7. Extension Points

Configuration before code: **item types, ID patterns, link types and coverage rules are data**
in the trace schema, and a **profile** is data too — a second standard needs no engine
change (PRD goal 6). In code, the one planned extension is **an extractor** — another test
framework, another document format — behind `IExtractor`, named per item type in the
configuration. Collectors (slice 3 and after) will be the second. There is no plugin system
and none is planned until two extractors exist outside this repo.

## 8. Key Abstractions / Glossary

[`CONTEXT.md`](../../CONTEXT.md) is the glossary. The few a newcomer needs first: **item**,
**link**, **marker**, **trace schema** and **trace configuration**, **baseline** and
**frozen**, **change request**, **suspect**, **ledger** and **trace lock**, **pin**.

## 9. Decisions needed

None new here. Open ones live where they bite: the gate's stage-awareness and the quiet form
in [Surface Architecture § Decisions needed](surface-architecture.md); withdrawn items, ID
prefixes and the digest of a test function in the
[slice tracker](../progress/slice-1-product-repo-half.md); the ledger half — events,
work-product states, the signature loop — in [Data Architecture § Not yet
written](data-architecture.md).
