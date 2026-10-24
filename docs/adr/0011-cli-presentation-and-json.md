---
summary: ADR-0011 — semantic terminal styling and explicit versioned CLI JSON preserve judgments, plain reports, evidence limits and the existing table contract.
read_when:
  - changing terminal selection, command JSON, parser errors or the bundled agent workflow
  - changing output determinism or machine-readable compatibility
---

# ADR-0011 — CLI presentation and JSON

- **Status:** accepted, 2026-10-24
- **Amends:** surface architecture §6 output and §7 machine-readable output; blueprint
  CLI/render ownership and the plain-only help decision
- **Decided by:** the developer, approving the two-slice implementation plan

## Context

Plain deterministic reports serve scripts and agents. Terminal readers benefit from
semantic emphasis; agents need fields they can branch on without scraping prose.
The ledger's existing `qmstrace.table/1` is already a public document contract.

## Decision

Deliver terminal presentation first, then explicit `--json` on assessment commands.
Resolve styling per invocation/stream: nonempty NO_COLOR, then nonzero nonempty FORCE_COLOR,
then TTY with TERM other than dumb. Typer's public help extension points select Rich or
plain help. Renderers receive pure Style values; no environment or terminal access enters
render/core. Authored content is literal. Reports keep their layout and plain bytes.

Explicit JSON overrides styling and returns one `qmstrace.cli/1` document for successful
assessments, failed checks and handled usage/domain/internal errors. Parser validation
remains Typer's; an option-aware prepass selects output before it runs, respecting values
and `--`. Exit codes remain 0/1/2/3. Data is command-specific and projected explicitly,
with public IDs, titles, relative locations, provenance, findings and evidence notices.
No raw dataclass, operational root, traceback or raw internal exception is serialized.
JSON errors have stable usage/could-not-judge/internal categories and a next move.

JSON is opt-in even in a pipe. Quiet changes human layout only. Help/version stay eager,
plain with JSON selected, and read no maps. Writing commands reject JSON before writes.
The table command's redundant JSON flag preserves its existing stdout bytes; the flag
cannot combine with --out. Without that flag its existing write behavior is unchanged.

Determinism is within a presentation mode; ANSI-stripped reports equal plain bytes.
JSON uses UTF-8, two spaces, one newline, no generated time or absolute operational paths.
Additive fields keep /1; removed/renamed fields or changed types/meaning require /2.
The machine-readable schema ships in the wheel and manual. The bundled skill documents
workflow and evidence interpretation; configuration remains authoritative.

## Consequences

Terminal layout does not become a second assessment engine. Existing public imports and
plain behavior reports remain compatible; help goldens add the JSON option. No runtime
dependency, new judgment, interactive UI or recording of approval is introduced.
The existing tag and unpublished release draft are left unchanged until a separately
requested release rebuild follows review and merge.

## Rejected alternatives

- Automatic JSON for pipes: breaks existing consumers and makes redirection change format.
- Styling completed prose: loses semantic distinctions and can color authored text as code.
- Dumping Assessment: leaks operational paths and repeats internal graph/configuration state.
- Wrapping table JSON: breaks an existing versioned contract without adding evidence.
- Treating exit zero as verification success: informational reports may contain failures.
- New filtering, pagination, streaming or write receipts: deferred until a concrete workflow
  needs them; targeted commands and shell projections bound agent context now.
