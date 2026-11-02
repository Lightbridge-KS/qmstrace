"""Select the independently versioned distribution and notes for a release tag.

Run from the repository root. This prepares files only; CI owns draft creation.
"""

import argparse
import re
import tomllib
from pathlib import Path


def prepare(tag: str) -> tuple[str, str, str]:
    plugin = tag.startswith("qmstrace-lang-csharp-v")
    package = "qmstrace-lang-csharp" if plugin else "qmstrace"
    prefix = "qmstrace-lang-csharp-v" if plugin else "v"
    root = Path("packages/qmstrace-lang-csharp") if plugin else Path(".")
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    if tag != prefix + version or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("tag must match the selected manifest release version")
    changelog = (root / "CHANGELOG.md").read_text()
    match = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", changelog, re.M | re.S
    )
    if match is None or not match[1].strip():
        raise ValueError("selected package changelog has no release notes")
    return package, version, match[1].strip() + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package, version, notes = prepare(args.tag)
    args.notes.write_text(notes, encoding="utf-8")
    args.output.write_text(
        f"package={package}\nversion={version}\n"
        f"wheel={package.replace('-', '_')}-{version}-py3-none-any.whl\n",
        encoding="utf-8",
    )
