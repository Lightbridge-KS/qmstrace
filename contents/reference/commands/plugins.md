# plugins

!!! abstract "TL;DR"
    Inspect installed extractor packages and compatibility problems without importing handlers
    or opening a traced repository. Installation and successful discovery do not prove extraction.

```text
--8<-- "cli/golden/help-plugins.txt"
```

Use `qmstrace plugins --json` for `qmstrace.cli/2` data. The result lists distributions,
versions, declared extractor names, API majors, parser dependencies and admission problems.
An unrelated rejected provider does not block inspection or a Python assessment. Selecting
an absent, rejected or ambiguous extractor refuses assessment with exit 2.

C# needs `qmstrace-lang-csharp` in the same environment as the host. See
[installation](../../how-to/install.md) for paired-wheel installation.
