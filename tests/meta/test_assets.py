"""Package data — what ships beside the code must be readable from the installed package.

The load-bearing claim: a file under `qmstrace/assets/` is reachable with
`importlib.resources`. The pipeline repeats this against the built wheel.
"""

from importlib.resources import files


def test_an_asset_is_readable_from_the_installed_package() -> None:
    text = (files("qmstrace") / "assets" / "README.md").read_text(encoding="utf-8")
    assert "What ships with the engine" in text
