# CLI JSON format

!!! abstract "TL;DR"

    Use `--json` for assessment data and handled errors. Read `format`, `exit_code`,
    `error` and `notices` before acting on `data`. `qmstrace.cli/2` is separate from
    the existing `qmstrace.table/2` document format.

## Selection

`--json` is accepted before the command or after its leaf, once. It is explicit; piping
without it keeps plain text. It overrides terminal styling. `-C` and `--workspace` retain
their existing placements and path anchors. `--quiet` does not remove JSON findings.
Help and version remain eager plain text when JSON is selected and read no workspace.

| Commands | Data |
|---|---|
| `status` | Scan counts, requirement classification, sources, baselines and suspect summary |
| `check`, `ledger check` | Counts, gate mode, violations, gaps, all suspect reasons and baseline evidence |
| `rules` | Effective schema, rule conditions, ownership and local declarations |
| `paths` | Selection provenance, map filename, logical locations and availability |
| `thread`, `ledger thread` | Item records and directional steps with distances, parents and links |
| `impact`, `ledger impact` | Starts, downstream groups, origins and candidate impact IDs |
| `results` | Reports, verdicts, tests/runs, duplicates, unmatched entries and verification methods |

`init`, `graph` and `ledger copy-schema` reject JSON before writing.
`ledger table --json` is a redundant alias for its established stdout table document;
`--json --out FILE` is refused before assessment or writes. Without `--json`, table `--out`
retains its existing behavior. See [the table format](table-format.md).

## Envelope and schema

The [downloadable JSON Schema](../assets/qmstrace-cli.schema.json) defines the envelope
and all command payloads. An identical `assets/cli.schema.json` ships inside the Python
package. Objects allow additive keys; consumers must ignore unknown keys.

| Field | Contract |
|---|---|
| `format` | `qmstrace.cli/2` |
| `command` | Canonical command, such as `ledger check`; null if no command was recognized |
| `scope` | `local` or `project`; null if scope was not established |
| `exit_code` | Same value as the process exit |
| `data` | Command payload, or null when the invocation could not produce a view |
| `notices` | Evidence/provenance strings; never hidden by quiet mode |
| `error` | Null for a completed view; otherwise `category`, `message` and `next_move` |

A configuration-only paths view:

```json
--8<-- "cli/golden/json-paths.json"
```

Error categories are `usage`, `could-not-judge` and `internal`. A failed check is a completed
assessment: exit `1`, populated data, `error: null`. Exit `2` means usage or inability to
judge; exit `3` means an internal fault. Exit `0` on `results` may contain failing tests.
See [exit codes](exit-codes.md).

An unseen starting ID rejects the whole impact request; it produces no candidate or partial
reach:

```json
--8<-- "cli/golden/json-could-not-judge.json"
```

Handled outcomes emit one complete document on stdout, including nonzero exits. There is
no human preamble, duplicate stderr diagnostic or traceback. Operating-system termination,
interrupts and a broken output stream cannot promise a complete document.

## Migration from CLI /1

All `--json` outcomes in 0.3.0 use `/2`, including v1 input and parser errors before
repository discovery. Locations replace display strings with records. `rules.repos` exposes
`ledger_repo` and `members`, while `version`, `repo` and `workspace_profile` describe the
input's identity/selection contract. V1 rules keep their meaning and path defaults internally;
they are not converted into dummy v2 configuration. No output `/1` selector is provided.

## Values and compatibility

JSON is UTF-8 with two-space indentation and one trailing newline. Ordering is deterministic
for identical inputs. There is no generated timestamp. Source tag dates and report digests
are evidence and remain present. IDs retain their authored or repo-qualified form; unknown
node types remain null. Public locations are records with `repo`, an internal `path`, and nullable `line`, not
operational roots. A legacy/unidentified repo is null; a legacy relative label can still
identify evidence whose owner was not declared. Do not reconstruct native checkout roots
from these records. V2 local identity is explicit; project source records name their repo.
Authored titles and report details remain literal content, including brackets.

Baseline comparisons and suspect reasons reference a governing baseline by scope, subject,
commit and tag names; full tag metadata is in the governing baseline records. Results list
tests and cases once, with ID references from requirement rows. `other_methods` carries
`evidence_only: true`; those test outcomes do not approve another declared method.

An added key keeps `/1`. Removing or renaming a field, changing its type, meaning or an
established ordering requires `/2`. The format does not persist results or record review.
