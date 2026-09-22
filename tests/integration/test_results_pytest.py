"""Use real pytest output to check the reader, identity convention and duplicate semantics."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from qmstrace.workspace import Workspace


@pytest.mark.parametrize("family", ["xunit1", "xunit2"])
def test_real_pytest_families(project: Path, family: str) -> None:
    root = project / "service"
    source = root / "tests/unit/test_report.py"
    source.write_text("""import pytest

@pytest.mark.verifies("REQ-SVC-01")
@pytest.mark.parametrize("value", [1, 2], ids=["a[b]", "x]y["])
def test_parameter(value):
    assert value

@pytest.mark.verifies("REQ-SVC-01")
class TestOuter:
    class TestInner:
        def test_method(self): pass

@pytest.fixture
def broken_setup():
    raise ValueError("setup failed")

@pytest.fixture
def broken_teardown():
    yield
    raise ValueError("teardown failed")

@pytest.mark.verifies("REQ-SVC-02")
def test_error(broken_setup): pass

@pytest.mark.verifies("REQ-SVC-02")
def test_two_failures(broken_teardown):
    assert False, "body failed"

@pytest.mark.verifies("REQ-SVC-02")
@pytest.mark.skip(reason="not available")
def test_skip(): pass

@pytest.mark.verifies("REQ-SVC-02")
@pytest.mark.xfail(reason="known failure")
def test_xfail(): assert False

@pytest.mark.verifies("REQ-SVC-02")
@pytest.mark.xfail(reason="now passes")
def test_xpass(): pass

@pytest.mark.verifies("REQ-SVC-02")
@pytest.mark.xfail(strict=True, reason="must still fail")
def test_strict_xpass(): pass
""")
    (root / "pytest.ini").write_text("[pytest]\nmarkers = verifies: direct trace targets\n")
    env = {key: value for key, value in os.environ.items() if key != "PYTEST_ADDOPTS"}
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest.ini",
            "-o",
            f"junit_family={family}",
            "--junitxml=report.xml",
            "tests",
            "-q",
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 1, done.stdout + done.stderr
    view = Workspace.open(root).results(root / "report.xml")
    assert not view.unmatched
    assert view.matched_cases == view.scanned_cases == 12
    assert view.entries == 15 and view.runs == view.matched_runs == 14
    assert view.duplicates == 1
    tests = {
        test.id.rsplit("::", 1)[-1]: test for target in view.requirements for test in target.tests
    }
    assert len(tests["test_parameter"].runs) == 2
    assert tests["test_method"].verdict == "pass"
    assert tests["test_xfail"].verdict == tests["test_skip"].verdict == "skip"
    assert tests["test_xpass"].verdict == "pass"
    assert tests["test_strict_xpass"].verdict == tests["test_error"].verdict == "fail"
    duplicate = tests["test_two_failures"].runs[0]
    assert duplicate.entries == 2 and duplicate.kinds == ("error", "failure")
    assert any("teardown failed" in detail for detail in duplicate.details)
