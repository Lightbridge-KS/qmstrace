# qmstrace-lang-python

Trusted, synchronous Python module and pytest source extraction for `qmstrace.plugin_api.v1`.
Requires Python 3.13+ and qmstrace 0.4.0+ with API v1 support. This package owns the
`python-module` and `pytest` extractor names. It uses standard-library `ast`; it does not
import scanned source or require pytest at runtime.

After publication, download both wheels from the private GitHub releases and install into
one tool environment:

```sh
uv tool install --with ./qmstrace_lang_python-0.1.0-py3-none-any.whl ./qmstrace-0.4.0-py3-none-any.whl
qmstrace plugins
```

Installation in an unrelated environment does not make the provider visible to qmstrace.
Existing trace configurations retain their extractor names. Digests use the executing Python
runtime's AST representation; retain that runtime version and exact package constraints with
evidence. Cross-minor digest equality is not promised.

From the workspace root, `uv sync` installs the host and both language packages editably.
`uv run pytest` runs compatibility tests. Build independently with
`uv build --package qmstrace-lang-python --wheel --no-sources`.
The workspace lock proves one development combination, not all released combinations.

The former `qmstrace.extract.python`, `qmstrace.extract.python_module` and
`qmstrace.extract.pytest_tests` imports are removed. Plugins use the public API v1 contract;
applications use the host CLI and catalog rather than the former internal call shapes.

The manifest owns the version. Tags use `qmstrace-lang-python-vX.Y.Z`; CI drafts releases
and humans publish them. Preparing a version does not publish it.
