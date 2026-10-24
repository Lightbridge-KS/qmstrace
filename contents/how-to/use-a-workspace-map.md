# Use a workspace map

!!! abstract "TL;DR"

    Write one local TOML map for the current checkouts, select it and run `qmstrace paths`.
    Then run the usual local or ledger check. The project's schema and copied rules stay
    the same across layouts.

For v2, set the local `workspace_profile` stem and use that filename for the user map.
Explicit/environment/ancestor selectors override it. The unique user-match route below is
for v1; v2 reads exactly its named file. See [v2 migration](migrate-to-names-only.md).

## Steps

1. **Create a local map.** In a folder containing the miniature `MINI` project's `ledger`,
   `service` and `client` checkouts, create `.qmstrace/workspace.toml`:

    ``` toml
    version = 1
    project = 'MINI'
    ledger_repo = 'ledger'

    [repos]
    ledger = '../ledger'
    service = '../service'
    client = '../client'
    ```

    Use the project's name and stable repo names. Adjust paths from the map's directory;
    include the current checkout and ledger role. List every checkout needed for a whole
    project check. Keep this machine's map local.

    If the map is inside a Git repo, follow [exclude the local map from Git](#exclude-the-local-map-from-git)
    before staging changes.

2. **Inspect it from the product root.** From `service`, select it explicitly:

    ``` sh
    qmstrace --workspace ../.qmstrace/workspace.toml paths
    ```

    Review the selection source, ledger and member locations. Resolve unexpected or
    unavailable locations in the map, then repeat. The
    [paths reference](../reference/commands/paths.md#with-a-workspace-map) shows the
    separate `SPLIT` fixture's output; the `MINI` map here is an input example.

3. **Keep the selection for the shell**, or continue supplying the flag on each command:

    ``` sh
    export QMSTRACE_WORKSPACE=../.qmstrace/workspace.toml
    qmstrace check --quiet
    ```

    This relative environment value is interpreted from each command's effective directory.
    After changing directory or using `-C`, adjust it accordingly. To rely on automatic
    discovery instead, unset it and leave the map at the common ancestor location:

    ``` sh
    unset QMSTRACE_WORKSPACE
    qmstrace paths
    ```

4. **Check the whole project from the ledger root.** From `ledger`:

    ``` sh
    qmstrace --workspace ../.qmstrace/workspace.toml ledger check --strict
    ```

    The map locates members; the ledger command retains its scope and refuses unread
    members. For schema updates, run `ledger copy-schema` with the same selection in the
    ledger — [share the project's schema](share-the-schema.md).

5. **For user-level discovery**, put a map in `~/.qmstrace/workspaces/` with a `.toml`
   extension, recalculate its relative entries from that directory, and remove any explicit
   or environment selector when checking discovery with `qmstrace paths`. It must match
   both the project and the current canonical trace root. Resolve malformed files or
   multiple matches before retrying; an explicit selector chooses a particular map.

The [workspace-map reference](../reference/workspace-maps.md) defines every selection
stage, refusal and path boundary. To return to tracked defaults, remove the active
selector and relocate matching automatic maps outside their discovery locations, then
confirm the defaults with `qmstrace paths`.

## Exclude the local map from Git

1. In each repo containing a local `.qmstrace/workspace.toml`, find its local exclude file:

    ``` sh
    git rev-parse --git-path info/exclude
    ```

2. Add this line to that file for a machine-local exclusion, or to the repo's `.gitignore`
   when the team adopts the convention:

    ``` gitignore
    /.qmstrace/workspace.toml
    ```

    Exclude this map file specifically. Other content under `.qmstrace/` may have a
    different owner. Check the exclusion with:

    ``` sh
    git check-ignore --no-index -- .qmstrace/workspace.toml
    ```

3. If the local map was already tracked, remove only its index entry and keep the local file:

    ``` sh
    git rm --cached -- .qmstrace/workspace.toml
    ```

4. Optionally track a generic template, such as `docs/examples/workspace-map.toml`, using
   only the miniature project's names and relative stand-ins. Copy and adapt it locally;
   that example path is not an automatic discovery location. Keep actual checkout roots
   out of the tracked template.

## Use a temporary map in CI

1. Check out the ledger and all required members. Supply their actual trace-root paths as
   job variables `MINI_LEDGER_ROOT`, `MINI_SERVICE_ROOT` and `MINI_CLIENT_ROOT`. The ledger
   variable must name the directory holding `qmstrace.schema.toml`, even when that is below
   the Git root. Install qmstrace and Python 3 in the job.

2. Generate a temporary map from those roots and select it explicitly for every command.
   This shell step uses native absolute paths as input; diagnostic locations remain
   relative. JSON string quoting keeps spaces, quotes and path separators valid in TOML:

    ``` sh
    workspace_map="$(mktemp)"
    trap 'rm -f "$workspace_map"' EXIT
    python3 - "$workspace_map" "$MINI_LEDGER_ROOT" "$MINI_SERVICE_ROOT" "$MINI_CLIENT_ROOT" <<'PY'
    import json
    import sys
    from pathlib import Path

    repo_roots = dict(zip(("ledger", "service", "client"), sys.argv[2:], strict=True))
    map_text = "version = 1\nproject = 'MINI'\nledger_repo = 'ledger'\n\n[repos]\n"
    map_text += "".join(
        f"{name} = {json.dumps(str(Path(root).resolve()), ensure_ascii=False)}\n"
        for name, root in repo_roots.items()
    )
    Path(sys.argv[1]).write_text(map_text, encoding="utf-8")
    PY
    qmstrace -C "$MINI_LEDGER_ROOT" --workspace "$workspace_map" paths
    qmstrace -C "$MINI_LEDGER_ROOT" --workspace "$workspace_map" ledger check --strict
    qmstrace -C "$MINI_SERVICE_ROOT" --workspace "$workspace_map" check --strict
    ```

    The explicit selector bypasses environment, ancestor and user-directory discovery.
    Keep the map in job scratch storage and let the cleanup remove it after the step.

3. For a product-only job, keep the existing no-map invocation when only that product is
   checked out, it carries a verified schema copy and no ambient selector applies:

    ``` sh
    unset QMSTRACE_WORKSPACE
    qmstrace -C "$MINI_SERVICE_ROOT" check --strict
    ```

    Unavailable ledger and sibling sources retain their existing visible notices; a local
    check does not claim whole-project verification. An explicitly selected partial map
    likewise leaves omitted members unavailable; it never fills them from defaults.
