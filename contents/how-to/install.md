# Install and pin extraction packages

!!! abstract "TL;DR"
    Only Markdown ships in the host. Python and C# each require a separate wheel in the same tool
    environment. Keep the selected wheels, exact dependency constraints and Python version with
    assessment evidence. The examples below target the prepared 0.4.0/0.1.0 release pair.

## Download and install

Prerequisites: Python 3.13+, uv, and authenticated GitHub CLI access to the private repository.
Run these commands in a download folder. Release availability depends on human publication;
preparing a version or running CI does not publish it.

```sh
gh release download v0.4.0 --repo Lightbridge-KS/qmstrace --pattern 'qmstrace-*.whl'
gh release download qmstrace-lang-python-v0.1.0 --repo Lightbridge-KS/qmstrace --pattern 'qmstrace_lang_python-*.whl'
gh release download qmstrace-lang-csharp-v0.1.0 --repo Lightbridge-KS/qmstrace --pattern 'qmstrace_lang_csharp-*.whl'
uv tool install --with ./qmstrace_lang_python-0.1.0-py3-none-any.whl --with ./qmstrace_lang_csharp-0.1.0-py3-none-any.whl ./qmstrace-0.4.0-py3-none-any.whl
qmstrace plugins
```

The extra wheel must be in the **host's** tool environment. Installing it in a separate
project environment has no effect on this command. An existing tool installation may need
`--force` to replace it. A host-only installation omits `--with`; Python and C# configurations then
refuse assessment, and their setup refuses before writing files. Default starter selection
still chooses Python, so it also requires the Python provider. For a single language, supply
only that language wheel with `--with`.

## Reproduce, upgrade and roll back

`uv tool dir` prints the tool-environment directory. Its qmstrace interpreter is
`qmstrace/bin/python` below that directory on POSIX, or `qmstrace/Scripts/python.exe` on
Windows. Set `TOOL_PYTHON` to that interpreter path. In a POSIX shell:

```sh
uv pip freeze --python "$TOOL_PYTHON" --exclude qmstrace --exclude qmstrace-lang-csharp --exclude qmstrace-lang-python > environment.constraints.txt
qmstrace plugins --json > plugins.json
```

Retain the Python version, all selected wheels and their SHA-256 hashes too. The constraints exclude
wheel paths intentionally; explicit wheel arguments pin the selected products. For an upgrade,
choose the new plugin wheel and keep the host wheel fixed. First test that pair in a separate
environment, then install with `uv tool install --force --constraints environment.constraints.txt
--with PLUGIN_WHEEL HOST_WHEEL`. If its dependencies cannot satisfy the retained constraints,
resolve and test a new environment explicitly. Do not silently loosen an evidence pin.

Rollback uses the same command with the retained earlier host/plugin wheels and their own
constraints. Retain dependency wheels for offline replay (`--no-index --find-links WHEELHOUSE`).
The shared development `uv.lock` does not establish compatibility for every released pair.

## Compatibility evidence

The repository's `just prepare-wheelhouse` downloads dependencies. After that, `just wheel`
verifies isolated installations outside the checkout and replaces only the plugin against an
unchanged host. The run writes artifact hashes and exact environments under `dist/compatibility-*.json`.
Linux, Windows and macOS CI retain these files. A fixture successor demonstrates the update
mechanism; it does not establish a historical release combination that has not shipped.

## Python migration

Existing `python-module` and `pytest` configuration names are unchanged. The old internal
`qmstrace.extract.python`, `qmstrace.extract.python_module` and `qmstrace.extract.pytest_tests`
imports are removed. The supported plugin boundary is `qmstrace.plugin_api.v1`. Pytest
is not required in the host environment: source is parsed, never imported. Preserve the
Python runtime version with evidence because AST-based digests can differ between runtimes.
When upgrading one plugin in a combined installation, repeat `--with` for the retained
other language wheel as well; the explicit arguments define the desired environment.
