---
summary: ADR-0007 — a component whose file has no type to document is marked in that file's own leading comment: a Razor page in the first `@* … *@` above its markup or code block, read by line and never by the C# parser; a `.cs` file of top-level statements in the comment block it opens with. A file that has a type is never read this way. One extractor still, no new configuration. Amends requirement REQ-QMT-21 (CR-006), DSN-QMT-15 and marker syntax v0.
read_when:
  - changing where a C# or Razor component's marker may be written, or adding another file shape
  - a marker in a Razor page is read, ignored or reported as a stray unexpectedly
  - deciding whether a non-C# file may be routed through the C# parser
---

# ADR-0007 — A file with no type to document

- **Status:** accepted, 2026-10-21
- **Amends:** requirement REQ-QMT-21, under CR-006;
  [codebase blueprint](../structure/codebase-blueprint.md) — DSN-QMT-15, whose title claimed C#
  is read from one parse; [data architecture](../design/data-architecture.md) *Marker syntax v0*
  (a row per new shape); extends [ADR-0004](0004-reading-csharp.md), which chose the doc-comment
  rule
- **Decided by:** the developer, 2026-10-21 (qmstrace issue #64)

## Context

ADR-0004 settled that a C# component is a `.cs` file marked in the leading `///` doc comment of
its **first type**. Two shapes a design register commonly names have no such type: a Blazor
`.razor` page, whose class is generated at build time, and a `Program.cs` written as top-level
statements. In the first C# project one design element names only an Admin Razor page, so it
stayed uncovered permanently although the page exists and realises it; three more name a Razor
component or `Program.cs` beside C# classes, and closed through the classes while the register's
other named components dropped out of the chain with nothing said. The only workaround was a
code-behind class existing solely to hold a comment — product code written for the tool.

Probing the engine before deciding established two facts that shaped this:

| Input | `error` | `types` | `comments` | Produced |
|---|---|---|---|---|
| top-level statements with `// Implements: …` | `None` | none | the line | a component, no link, and the marker kept as a **stray** |
| `@* Implements: … *@` in a `.razor` | `None` | none | none | a component, **no link, no stray, no finding** |
| a `.razor` whose markup puts a `///` field line in an error span | set | none | — | **V08, and no item at all** |

So the marker on a top-level `.cs` file was already in hand and deliberately discarded, while
the Razor marker was never seen. And routing a `.razor` file through the C# parse is unsafe:
`_READ_TEXT` in `extract/csharp/_syntax.py` treats a `///` field line inside an error span as a
parse error in something read, so whether such a file is refused depends on where its markup
happens to sit, and an unrelated edit can flip a read file into a refused one.

## Decision

- **A file with no type to document is marked in its own leading comment.** A file that *has* a
  type is never read this way, so no `.cs` file that links today links differently, and a marker
  above a file's first type stays the stray it already was.

  | File | Where its marker goes |
  |---|---|
  | `.cs` with a type | the first type's leading `///` doc comment, as ADR-0004 settled |
  | `.razor` | the first `@* … *@` in the page's **head** |
  | `.cs` with no type | the comment block the file opens with, `//` or `///` |

- **A Razor page's head** is its leading run of blank lines, Razor comments and directives. The
  first line of markup, or the `@code`/`@functions` block, ends it. So the marker may sit above
  `@page "/clients"` or below it — both orders are written in practice, and a rule that admitted
  only one would make the common case a stray.

- **A Razor file is read by its lines, in `extract/csharp/_razor.py`, which imports neither
  `_syntax` nor tree-sitter.** The architecture test that pins the parser to one module keeps it
  that way. The digest covers the page's text with its Razor comments removed, giving the
  property the C# token digest exists for: layout and comments are not a change.

- **An unread marker in a Razor page is a stray, with its own wording.** Below the head, inside
  the code block, or written as `//`/`///` — which Razor renders as page text — all report. A
  Razor page's own copy is not a marker: as everywhere else, the key must be a link the item type
  carries and the value must hold a whole ID.

- **One extractor, one form.** `csharp-file` keeps its name and its registry entries, and a
  project widens its component type's `files` to `["src/**/*.cs", "src/**/*.razor"]`. The gap's
  next move names all three places, because a form is chosen per item type and never per file;
  every span it names round-trips through the extractor in the file shape it belongs to.

## Consequences

- REQ-QMT-21 gains the new shapes under CR-006; no new requirement, since the claim — a C# repo
  is read where its markers are authored — is unchanged and merely reaches further.
- **DSN-QMT-15 is retitled.** "C# is read from one parse, by two extractors" is no longer true: a
  Razor file is read deliberately without that parse. The element keeps its ID; its digest moves,
  so its dependants are suspect until reviewed, which amending the body alone would have cost
  anyway.
- No configuration change, so no project's schema or its digest moves, and the five extractor
  names are untouched.
- A gap's next move is longer, naming three places instead of one. That is the price of a form
  per item type; it replaces a next move that, for a Razor page, could not be followed at all.
- **Known limitation:** a marker inside a Razor page's `@code { }` block is a C# comment in a file
  this reader scans by line. It is reported as a stray, not read — which is the right outcome, but
  it is reported by position rather than by understanding the block.
- **Docs that follow:** marker syntax v0, the blueprint's DSN-QMT-15, the configuration
  reference's extractor table, the C# how-to, the packaged skill, the scenario catalogue.

## Rejected alternatives

- **A code-behind partial class per Razor page.** Works with ADR-0004 unchanged, and is what the
  adopter does today. It costs a file per page whose only purpose is to hold a comment, and makes
  the trace a reason to shape product code.
- **Routing `.razor` through the C# parser anyway**, reading `///` lines from it. No new module,
  and the existing field-line reader would serve — but the probe above shows the file is refused
  or read depending on where its markup sits, so the same page could pass today and be V08 after
  an edit that has nothing to do with the marker.
- **A second item type for Razor components**, with its own extractor, added to the `Implements`
  link's sources. Expressible today with no engine change at all, but it splits "component" in
  two for every schema, every coverage rule and every table column, to describe one thing.
- **A generic reader with a comment prefix set per item type** — the issue's third row, which
  would also cover systemd units, YAML and shell. `[items.*]` admits no key beyond the five it
  reads, so this needs a new configuration key and a new concept; a C# file with no type is not
  that concept. Filed separately.
- **Reading a file's leading comment as a fallback when its first type carries no marker.** More
  forgiving, and it would let a marker sit at the top of any file. It silently changes behaviour
  for every existing C# repo: a leading comment saying `Implements:` is a reported stray today
  and would quietly become a live link.
- **Requiring the Razor comment to be the file's first content.** The most literal reading of
  "only the leading comment is read", and the issue's own example. Every Razor scaffold writes
  `@page` first, so the common case would have been a stray.
