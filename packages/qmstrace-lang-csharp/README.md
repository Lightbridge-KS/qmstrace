# qmstrace-lang-csharp

Trusted, synchronous C# and Razor extractors for `qmstrace.plugin_api.v1`.
Requires Python 3.13+ and qmstrace 0.4.0+ with API v1 support. This package owns the
`csharp-file` and `xunit` extractor names and both tree-sitter dependencies.

Download the host and plugin wheels from their private GitHub draft/published releases
as authorized. Install published wheels together:

```sh
uv tool install --with ./qmstrace_lang_csharp-0.1.0-py3-none-any.whl ./qmstrace-0.4.0-py3-none-any.whl
qmstrace plugins
```

Installation into an unrelated environment does not make the plugin visible to qmstrace.
Existing C# trace configuration and TRX reports retain their meaning. Parser versions affect
extraction, so retain the exact environment constraints with audit evidence.

From the workspace root, `uv sync` installs the host and both language packages editably. `uv run pytest` exercises
the extraction reference cases and plugin seam. Build this package independently with
`uv build --package qmstrace-lang-csharp --wheel --no-sources`. The workspace lock represents
one development combination, not all supported released combinations.

See the repository's extensibility design and implementation tracker for the contract,
compatibility matrix and evidence limits. Each package has its own version and changelog;
plugin tags use `qmstrace-lang-csharp-vX.Y.Z`. Releases remain human-published GitHub drafts.
