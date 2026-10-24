# Names-only configuration

!!! abstract "TL;DR"

    Version 2 puts repository identities and rules in Git, and checkout addresses in a local
    workspace map. Every v2 local file declares `repo` and `workspace_profile`. Version 1
    remains readable with its original defaults and historical meaning.

## Shared schema

The ledger authors `qmstrace.schema.toml`. Its membership is names only:

```toml
version = 2
project = "MINI"

[repos]
ledger_repo = "ledger"
members = ["ledger", "service", "client"]
```

Existing item types, links, rules, external source paths, baselines and table settings follow.
`members` is a nonempty set: duplicates are refused and order does not affect its digest.
Names preserve case and use letters, digits, underscores, dots and hyphens, starting with a
letter or digit. They cannot contain a path separator or colon. The ledger role must be a
member when it declares traced items; a schema-only ledger can remain outside the member set.

## Local identity

A product's `qmstrace.toml` starts with these fields, outside its generated schema block:

```toml
version = 2
repo = "service"
workspace_profile = "mini-service"
```

The ledger declares its own identity and reads its schema:

```toml
version = 2
repo = "ledger"
workspace_profile = "mini-service"

[schema]
path = "qmstrace.schema.toml"
```

The existing `[subjects]` and `[items]` declarations remain local. `repo` must be a member or
the ledger role. `workspace_profile` is required and matches `[a-z0-9][a-z0-9_-]*`: no directory
or `.toml` suffix. The filename is a default selector, not a second project identity.

`ledger copy-schema` writes schema version 2, the names-only `[schema.repos]`, the rules and
the verified digest into each selected product. Local and schema versions must agree for
assessment. A v2 file refuses the legacy local `ledger` pointer and path-valued membership.

## Local maps and selection

The map itself retains **version 1**. For example, a developer's
`~/.qmstrace/workspaces/mini-service.toml` can contain:

```toml
version = 1
project = "MINI"
ledger_repo = "ledger"

[repos]
ledger = "/work/records/solution"
service = "/work/apps/backend"
client = "/work/clients/frontend"
```

Map entries are native absolute paths or relative to the map's canonical containing directory.
Selecting a symlink uses its target's directory. Values never expand `~` or environment
variables. Native Windows paths may span drives; TOML literal strings such as
`service = 'D:\apps\backend'` avoid backslash escaping.

The precedence is explicit `--workspace FILE`, nonempty `QMSTRACE_WORKSPACE`, nearest ancestor
`.qmstrace/workspace.toml`, then exactly the named user file. Unrelated user files are unread.
No map sources merge. A selected map must bind the current root under its exact `repo` name;
available mapped roots must declare coherent identities. Unknown names, duplicate physical
roots, wrong projects and swapped identities are errors.

An absent implicit profile permits local evidence from the committed schema. Other repos
remain unavailable and notices remain visible. A malformed, unreadable, stale-bound or dangling
profile is exit `2`; explicitly selecting an absent file is also an error. Project operations
require every assessed member. Targeted schema copying requires every selected destination.

A configuration-only view from the miniature project's v2 fixture:

```json
--8<-- "cli/golden/v2-paths.json"
```

## Evidence and compatibility

CLI `--json` uses `qmstrace.cli/2`; tables use `qmstrace.table/2`, for **both** input versions.
Source locations contain `repo`, `path` and `line`, independent of native checkout addresses.
Human project locations use labels such as `service:src/service/keys.py:7`. These are evidence
labels, not paths to join to the invocation directory. IDs and configured rules keep their
meaning. See [CLI JSON](cli-json.md) and [table format](table-format.md).

A map cannot repair `[schema] path`, change a schema digest, substitute current rules for a
tagged tree or redirect a product invocation to ledger scope. Historical v1/v2 configurations
are read from their own trees. Converting v1 membership to v2 changes the shared digest once;
subsequent relocations change only local maps.

`init` still creates v1 starters and refreshes valid v2 setups. Follow
[migrate to names-only configuration](../how-to/migrate-to-names-only.md) for explicit bootstrap.
