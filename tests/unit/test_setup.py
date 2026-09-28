import configparser
import tomllib

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.setup import MARKER, guide, pytest_section, register_marker


@pytest.mark.parametrize(
    "markers",
    [
        '["slow: expensive"]',
        '[\n"slow: expensive",\n]',
        '"slow: expensive"',
        '"""slow: expensive\nnetwork: live"""',
    ],
)
def test_toml_marker_values_preserve_settings(markers: str) -> None:
    source = '[tool.pytest.ini_options]\naddopts = "-q"\nmarkers = ' + markers + "\n[other]\nx=1\n"
    result = register_marker("pyproject.toml", source, "tool.pytest.ini_options")
    data = tomllib.loads(result)
    assert data["tool"]["pytest"]["ini_options"]["markers"][-1] == MARKER
    assert data["tool"]["pytest"]["ini_options"]["addopts"] == "-q"
    assert data["other"] == {"x": 1}
    assert register_marker("pyproject.toml", result, "tool.pytest.ini_options") == result


@pytest.mark.parametrize(
    "source",
    [
        "[pytest]\nmarkers = slow: expensive",
        "[pytest]\nmarkers =\n    slow: expensive\n[other]\nx=1\n",
    ],
)
def test_ini_preserves_existing_marker(source: str) -> None:
    result = register_marker("pytest.ini", source, "pytest")
    config = configparser.ConfigParser()
    config.read_string(result)
    assert "slow: expensive" in config["pytest"]["markers"]
    assert MARKER in config["pytest"]["markers"]
    assert register_marker("pytest.ini", result, "pytest") == result


@pytest.mark.verifies("DSN-QMT-11")
def test_managed_block_preserves_surrounding_bytes() -> None:
    source = "before\n<!-- qmstrace:begin -->\nold\n<!-- qmstrace:end -->\nafter\n"
    block = "<!-- qmstrace:begin -->\nnew\n<!-- qmstrace:end -->\n"
    assert guide(source, block) == source.replace("old", "new")
    assert guide("before", block).startswith("before\n\n")


def test_invalid_config_refused() -> None:
    for name, source in [("pyproject.toml", "bad = ["), ("pytest.ini", "no section")]:
        with pytest.raises(CouldNotJudge):
            pytest_section(name, source)
    with pytest.raises(CouldNotJudge):
        register_marker("pytest.toml", "[pytest]\nmarkers = 1\n", "pytest")
    with pytest.raises(CouldNotJudge):
        register_marker("pytest.toml", '["pytest"]\n', "pytest")
    assert pytest_section("tox.ini", "[other]\nx=1") is None


def test_ini_case_and_indentation_preserve_registration() -> None:
    import configparser

    from qmstrace.core.setup import MARKER, register_marker

    source = "[pytest]\nMarkers =\n    slow: expensive\naddopts = -q\n"
    result = register_marker("pytest.ini", source, "pytest")
    parser = configparser.ConfigParser()
    parser.read_string(result)
    assert "slow: expensive" in parser["pytest"]["markers"]
    assert MARKER in parser["pytest"]["markers"]
    assert register_marker("pytest.ini", result, "pytest") == result
