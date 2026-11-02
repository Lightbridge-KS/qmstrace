"""Enforce the existing 90% production coverage floor independently for all production wheels."""

import json
from pathlib import Path

report = json.loads(Path("dist/coverage.json").read_text())
for prefix in (
    "src/qmstrace/",
    "packages/qmstrace-lang-csharp/src/qmstrace_lang_csharp/",
    "packages/qmstrace-lang-python/src/qmstrace_lang_python/",
):
    summaries = [
        v["summary"] for k, v in report["files"].items() if k.replace("\\", "/").startswith(prefix)
    ]
    assert summaries, f"No coverage measured for {prefix}"
    statements = sum(v["num_statements"] for v in summaries)
    covered = sum(v["covered_lines"] for v in summaries)
    percent = 100 * covered / statements
    assert percent >= 90, f"{prefix}: {percent:.2f}% below 90%"
    print(f"{prefix}: {percent:.2f}% ({covered}/{statements})")
