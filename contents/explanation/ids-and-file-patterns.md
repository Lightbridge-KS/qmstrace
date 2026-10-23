# IDs and file patterns

!!! abstract "TL;DR"

    The project decides what its own IDs and names look like, and each repo decides what its
    items' IDs look like and where its documents live. qmstrace fixes only the general shape of
    every ID: capital letters and digits in hyphen-joined segments, ending in a number that may
    carry dotted parts, such as `REQ-SVC-01` or `TC-SVC-04.1-01`. An ID pattern can narrow that
    shape but never widen it. Documents can move at
    any time. An ID frozen by a baseline cannot change.

## Who decides what

| What | Decided by | Set in |
|---|---|---|
| the shape of every ID | qmstrace | nowhere: it is built in |
| the ID pattern of requirements and design elements | the product repo | `[items.<type>]`: `id_pattern`, `id_prefix` |
| the files each type is read from | the product repo | `[items.<type>]`: `files`, `ignore` |
| the subject, and its key inside IDs | the product repo | `[subjects.<name>]`: `key` |
| the ID of a module or a test | nobody: it is derived | the module's path; the test's node ID |
| the agreement's clause IDs, and how the agreement declares them | the project | `[externals.<name>]`: `prefix`, `source`, `declared_as` |
| change-request IDs, where they are kept, the accepted state | the project | `[change_requests]`: `prefix`, `source`, `accepted` |
| the names of links and fields | the project | `[links]`; `[item_types.<type>]`: `required`, `values` |
| which tags are baselines | the project | `[baselines.<name>]`: `tag`, `covers`, `subject` |

The split follows who can change a thing without asking anyone else.

- **The repo's own business:** where it keeps its SRS, and how it numbers its own requirements.
- **The project's:** what a link means, which clauses exist, and which tags freeze what. Every
  product repo of the project must read these the same way, so they are written once, in the
  ledger's trace schema. Each repo holds that schema by path or as a verified copy.

A repo cannot change a project setting in its copy. The copy is checked against its digest,
so an edit made by hand is refused. The project side changes the setting and
[generates the copy again](../how-to/share-the-schema.md). The keys themselves are in the
[configuration reference](../reference/configuration.md).

`qmstrace rules` prints what is in force, divided by owner the same way. Here it is for the
fixture project's service repo:

``` text
--8<-- "cli/golden/rules-service.txt"
```

## One shape for every ID

Every ID, of any type and from any source, has one shape:

``` text
[A-Z][A-Z0-9]*(-[A-Z0-9]+(\.[0-9]+)*)*-[0-9]+(\.[0-9]+)*
```

| Written | An ID? |
|---|---|
| `REQ-SVC-01`, `SWR-GW-001`, `SRS-FR-12`, `AGR-7`, `CR-003` | yes |
| `TC-SVC-04.1-01`, `DSN-SVC-04.1` | yes: a number may carry dotted parts |
| `REQ-SVC-01.` at the end of a sentence | `REQ-SVC-01`: the full stop is not part of it |
| `TC-SVC-03.1a` | no — and never `TC-SVC-03`: an ID is read whole or not at all |
| `REQ-SVC-01A` | no: a letter after the number |
| `REQ_SVC_01` | no: underscores |
| `req-svc-01` | no: lower case |
| `3.2.1`, `FR.12` | no: no hyphen-joined segments |

**Why the shape is fixed.** A repo meets many IDs it has no pattern for:

- a sibling's `REQ-CLT-07`;
- a clause `AGR-3` from the agreement;
- a change request `CR-001`;
- IDs mentioned in prose, tables and diagrams.

One shape lets qmstrace recognise all of them without knowing whose they are. The repo's
patterns then decide which of those IDs are its own items. Every other ID of that shape is
cited, not declared.

**A pattern narrows the shape; it cannot widen it.** Take `^REQ_SVC_\d{2}$`: no ID can start
the way it does, so it would match nothing, silently. qmstrace refuses such a pattern when it
reads the configuration, with exit code `2`, and says why. It refuses a prefix that no ID can
start with in the same way.

**The shape is not unique to IDs.** `SHA-256`, `UTF-8` and `IEC-62304` fit it too. That is why
an ID declares an item only in one place, first in a heading. In prose, in tables and later in
a heading, qmstrace checks only IDs of this repo's own kind (`V16`).

## A pattern, and the start it shares

A requirement or a design element has an ID that someone writes, so its type needs an
`id_pattern`. The pattern can be any regular expression within the shape: `^REQ-SVC-\d{2}$`,
`^SWR-GW-\d{3}$`, or `^REQ-SVC-\d{2,3}$` to allow three digits.

Every ID of one type also starts with the same literal text, `REQ-SVC-` in the first pattern.
qmstrace reads that text from the pattern, and uses it to tell a slip from prose:

``` mermaid
flowchart LR
  h["heading<br/>REQ-SVC-3 …"] --> own{"matches<br/>id_pattern?"}
  own -- yes --> item["declares<br/>the item"]
  own -- no --> kind{"starts like<br/>this repo's IDs?"}
  kind -- yes --> v02["V02<br/>a malformed ID"]
  kind -- no --> prose["an ordinary heading<br/>IEC-62304 …"]
```

"Starts like" means it has the same literal start, or the same first segment (`REQ`). A first
word that starts as an ID and runs on, such as `REQ-SVC-03b` or `REQ-SVC-04.1a`, counts as a
malformed ID too: `V02` names the whole word.

The start is proved across every branch, including groups. `^(REQ|RQ)-SVC-\d{2}$` shares
`R`; `^REQ-(SVC|CLT)-\d{2}$` shares `REQ-`. An explicit `id_prefix` may be shorter than the
proved start, but cannot name only one branch. For example,
`^(REQ|NFR)-SVC-\d{2}$` with `id_prefix = "REQ-"` is refused before scanning: the `NFR-`
branch would otherwise let a malformed heading disappear silently. A pattern with no provable
ID-shaped start is refused even if `id_prefix` is supplied. Rewrite it to put the shared start
first, or use separate item types for distinct ID families. Escaped literal characters count:
`^REQ-SVC-04\.1-\d{2}$` is valid, while `^FR\.\d{2}$` cannot produce an ID of the
required shape.

## The subject key

A subject is a named body of requirements. Its key is capital letters and digits, and it
appears as one whole segment inside each of its IDs: `SVC` in `REQ-SVC-01`. Only a segment
between the first and the last counts.

A baseline freezes one subject, and the key is how qmstrace knows which subject an item belongs
to. **Ownership is never guessed.** For a document type a baseline could cover, a current ID
without exactly one matching subject-key occurrence and one configured owner is V17 while
authoring, even before the
first tag. `status` counts it and `check` lists it. If an applicable tag already exists, the
run stops with exit `2`: it cannot determine whether that item is controlled. An invalid ID
frozen in a selected tagged tree also exits `2` and names the tag. Correct the current tree
and establish a new approved baseline; renaming today's heading cannot change the old tag.

Ownership goes by the ID rather than by the file it sits in, because a file can move and an ID
cannot.

## Code and tests are already named

- **A module's ID is its path**, e.g. `src/service/keys.py`.
- **A test's ID is its pytest node ID**, e.g.
  `tests/unit/test_keys.py::test_a_call_without_a_valid_key_is_refused`.

These are the names the code and its test runner already use. A second, hand-written ID would
be one more thing to keep in step. qmstrace therefore refuses an `id_pattern` on these types,
because it would never be applied.

The cost is that renaming a module or a test function changes its ID, and what that should mean
for the trace is not settled yet. Baselines are not affected either way. They freeze
requirements and design elements, never modules or tests. After a baseline, a change to code
carries its change request by the project's commit or pull-request convention.

## Files can move

Each item type is read from the files its `files` globs name, less those its `ignore` globs take
back. The globs follow Python's standard library:

- `**` matches zero or more whole folders;
- `*` never crosses a `/`, so `docs/req/*-srs.md` does not reach `docs/req/old/a-srs.md`;
- case counts.

Inside Git, only the files Git lists are read: tracked, or untracked and not ignored. A
scratch note that Git ignores is never read, even if it quotes an item's heading.

**An item in a file its type is not read from is reported, not skipped.** Say the SRS moves and
its glob stays the same. Skipping its requirements silently would drop them from every coverage
rule. Instead, each one is a `V07`, and every link to one is a `V03`.

**Moving a file is not a change.** A baseline compares items by their ID and their text, never
by the path they are in. The text is the title and the section, with layout ignored. A tagged
tree is also read with the configuration it had at that tag, so the old glob finds the old
file. So renaming the SRS and updating its glob leaves every frozen requirement frozen, with no
violation.

## Choose the ID scheme before the first baseline

A frozen ID is permanent. Renaming it is not an edit but two separate events:

- the frozen item disappears: `V13`, a frozen item's heading was removed;
- a new item appears in a controlled scope: `V10`, added without a fresh change-request
  citation.

Retiring an item changes its status (`Status: withdrawn`), never its ID. See
[change a frozen item](../how-to/change-a-frozen-item.md).

So settle the ID pattern and the subject key before a baseline is cut. File names, folders
and globs stay free after it.

## The project's own IDs

**Agreement clauses** are declared in the agreement, a document the organisation writes in
whatever layout it uses. `declared_as` is a regular expression, applied line by line, whose one
group is the ID. The tool adapts to the document rather than the other way round.

The prefix decides where a citation is looked up. `Origin: AGR-3` starts with `AGR-`, so it is
looked up in the agreement, and a clause the agreement does not declare is `V09`. If the
agreement is reformatted and `declared_as` is not updated, the agreement declares nothing.
`check` then reports every cited clause as `V09`; it does not pass.

**Change requests:**

- Each one is a file in the ledger's change-request folder, named by its ID: `CR-001.md`.
- If its first heading starts with an ID, that ID must match the file name.
- Its `State:` and `Impacts:` lines come before the first prose section, so an example further
  down never grants approval.
- A `Change:` citation on an item must start with the project's prefix. `Change: SCR-001`, in a
  project whose prefix is `CR-`, is `V14`.

**Links and fields.** The link names `Origin`, `Satisfies`, `Implements`, `verifies` and
`Assumes` are keys in the schema's `[links]`. Required fields and their allowed values are
listed for each item type. Two field names belong to qmstrace itself, because it acts on them:
`Change`, which cites a change request, and `Status`, whose value `withdrawn` retires an item.

**Baselines** are tags the project already cuts. The schema gives the tag's pattern. The
subject is set in one of two ways:

- the tag names it, through a `(?P<subject>…)` group, as in `baseline/service/requirements/1`;
- the schema sets it, with `"*"` for every subject, as for a release tag like `v1.2.0`.

The tag names a subject by its name (`service`); an ID carries its key (`SVC`).

*Rejected:* one tag name imposed by qmstrace. It would ignore release tags that already are
baselines, and it could not handle one repo carrying several subjects. See
[baselines and change control](../reference/baselines.md).
