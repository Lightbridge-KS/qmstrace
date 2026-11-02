"""Each tag selects one manifest and changelog; no publication occurs in these checks."""

import runpy
import tomllib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "package,prefix,manifest",
    [
        ("qmstrace", "v", "pyproject.toml"),
        (
            "qmstrace-lang-csharp",
            "qmstrace-lang-csharp-v",
            "packages/qmstrace-lang-csharp/pyproject.toml",
        ),
    ],
)
def test_release_notes_follow_the_selected_manifest(package, prefix, manifest):
    version = tomllib.loads(Path(manifest).read_text())["project"]["version"]
    tag = prefix + version
    prepare = runpy.run_path(str(Path("scripts/release_metadata.py")))["prepare"]
    actual, stated, notes = prepare(tag)
    assert (actual, stated) == (package, version)
    assert notes.strip() and "## [Unreleased]" not in notes
    with pytest.raises(ValueError):
        prepare(tag + ".wrong")
