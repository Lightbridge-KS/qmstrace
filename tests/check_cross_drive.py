"""Native Windows acceptance: exercise installed CLI evidence across distinct drive roots.

Run after installing the candidate: python tests/check_cross_drive.py. This is a live
platform probe, not collected by pytest and not satisfied by POSIX path mocks.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    smoke = "--same-drive-smoke" in sys.argv[1:]
    if os.name != "nt" and not smoke:
        raise SystemExit("Native Windows is required; cross-drive acceptance was not run.")
    source = Path(__file__).resolve().parent / "fixtures/mini"
    candidates = [Path.home(), Path(tempfile.gettempdir())]
    candidates += [Path(f"{letter}:\\") for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ"]
    directories = (
        [tempfile.TemporaryDirectory(prefix="qmstrace-smoke-") for _ in range(2)] if smoke else []
    )
    bases = [Path(directory.name) for directory in directories]
    for candidate in [] if smoke else candidates:
        if not candidate.is_dir():
            continue
        canonical = candidate.resolve()
        if any(canonical.drive.casefold() == base.drive.casefold() for base in bases):
            continue
        try:
            directory = tempfile.TemporaryDirectory(prefix="qmstrace-native-", dir=canonical)
        except OSError:
            continue
        directories.append(directory)
        bases.append(Path(directory.name))
        if len(bases) == 2:
            break
    try:
        if len(bases) != 2:
            raise SystemExit(
                "Two distinct writable native drives are required; acceptance not run."
            )
        if not smoke:
            assert bases[0].resolve().drive.casefold() != bases[1].resolve().drive.casefold()
        roots = {
            "ledger": bases[0] / "records/solution",
            "service": bases[1] / "apps/backend",
            "client": bases[1] / "apps/frontend",
        }
        for name, root in roots.items():
            shutil.copytree(source / name, root)
        schema_file = roots["ledger"] / "qmstrace.schema.toml"
        schema = schema_file.read_text(encoding="utf-8")
        schema = re.sub(
            r"\[repos\][\s\S]*?(?=\[item_types)",
            '[repos]\nledger_repo = "ledger"\nmembers = ["service", "client"]\n\n',
            schema,
        )
        schema_file.write_text(schema.replace("version = 1", "version = 2", 1), encoding="utf-8")
        (roots["ledger"] / "qmstrace.toml").write_text(
            'version = 2\nrepo = "ledger"\nworkspace_profile = "native-fixture"\n'
            '[schema]\npath = "qmstrace.schema.toml"\n',
            encoding="utf-8",
        )
        for name in ("service", "client"):
            file = roots[name] / "qmstrace.toml"
            local = re.sub(r"^ledger\s*=.*\n", "", file.read_text(encoding="utf-8"), flags=re.M)
            local = local.replace(
                "version = 1",
                f'version = 2\nrepo = "{name}"\nworkspace_profile = "native-fixture"',
                1,
            )
            start = local.index("[schema]")
            end = local.index("[subjects", start)
            file.write_text(local[:start] + "[schema]\n\n" + local[end:], encoding="utf-8")
        profile = bases[0] / "map.toml"
        profile.write_text(
            'version = 1\nproject = "MINI"\nledger_repo = "ledger"\n[repos]\n'
            + "\n".join(f"{name} = {json.dumps(str(path))}" for name, path in roots.items()),
            encoding="utf-8",
        )
        env = {**os.environ, "QMSTRACE_WORKSPACE": str(profile), "NO_COLOR": "1"}
        cli = [sys.executable, "-c", "from qmstrace.cli import app; app()"]

        def run(name: str, *args: str, code: int = 0) -> str:
            result = subprocess.run(
                [*cli, "-C", str(roots[name]), *args],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            assert result.returncode == code, result.stdout + result.stderr
            rendered = result.stdout.replace("\\\\", "\\").replace("\\", "/").casefold()
            assert all(base.as_posix().casefold() not in rendered for base in bases), result.stdout
            return result.stdout

        run("ledger", "ledger", "copy-schema")
        for root in roots.values():
            for args in (
                ("init", "-q"),
                ("add", "-A"),
                (
                    "-c",
                    "user.name=Fixture",
                    "-c",
                    "user.email=fixture@example.invalid",
                    "commit",
                    "-qm",
                    "Native fixture",
                ),
            ):
                subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
        for command in ("paths", "rules", "status", "check"):
            value = json.loads(run("service", command, "--json"))
            assert value["format"] == "qmstrace.cli/2" and value["error"] is None
        for command in ("thread", "impact"):
            run("service", command, "REQ-SVC-01", "--json")
            run("ledger", "ledger", command, "REQ-SVC-01", "--json")
        run("ledger", "ledger", "check", "--strict", "--json", code=1)
        report = roots["service"] / "report.xml"
        shutil.copyfile(source.parent / "junit/service.xml", report)
        run("service", "results", "report.xml", "--json")
        table = json.loads(
            run("ledger", "ledger", "table", "matrix", "--report", f"service={report}")
        )
        assert table["format"] == "qmstrace.table/2"
        assert all(read["location"]["path"] == "." for read in table["read"])
        run("service", "graph", "REQ-SVC-01", "--out", "view.html")
        html = (roots["service"] / "view.html").read_text(encoding="utf-8")
        rendered_html = html.replace("\\\\", "\\").replace("\\", "/").casefold()
        assert all(base.as_posix().casefold() not in rendered_html for base in bases)
        run("ledger", "ledger", "copy-schema")
    finally:
        # TemporaryDirectory handles read-only Git objects on native Windows.
        for directory in directories:
            directory.cleanup()
    print(
        (
            "PASS: same-drive smoke (not native acceptance): "
            if smoke
            else "PASS: native distinct-drive "
        )
        + "paths/rules/status/check/thread/impact/"
        "results/table/graph/copy"
    )


if __name__ == "__main__":
    main()
