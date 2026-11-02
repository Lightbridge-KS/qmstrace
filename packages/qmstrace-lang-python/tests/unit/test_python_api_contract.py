"""Frozen pre-migration observations exercise the public API and host adapter."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest
from qmstrace_lang_python import module, pytest_tests

from qmstrace.core.findings import fix_stray
from qmstrace.plugin_api.v1 import ExtractRequest
from qmstrace.plugins.adapter import adapt, request
from qmstrace.plugins.catalog import Catalog

ROOT = Path(__file__).resolve().parents[4]
REFERENCE = json.loads((ROOT / "docs/progress/python-plugin-reference.json").read_text())


@pytest.mark.verifies("REQ-QMT-02", "REQ-QMT-15", "REQ-QMT-24", "DSN-QMT-17")
@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda c: c["name"])
def test_frozen_reference_outputs(case):
    cfg = Catalog().configuration(*((ROOT / p).read_text() for p in REFERENCE["configuration"]))
    is_test = case["name"] in ("pytest", "unread")
    kind = "automated_test" if is_test else "component"
    path = "tests/unit/test_keys.py" if is_test else "src/service/keys.py"
    source = request(path, case["source"], cfg.item_types[kind], cfg)
    handler = pytest_tests if is_test else module
    public = handler.extract(source)
    assert handler.extract(source) == public
    found = adapt(public, source)
    actual = json.loads(json.dumps(asdict(found)))
    for stray in actual["strays"]:
        stray["guidance"] = None  # previously host-owned; rendered guidance is checked below
    assert actual == case["extraction"]
    assert [fix_stray(s) for s in found.strays] == case["stray_guidance"]


@pytest.mark.verifies("REQ-QMT-02", "REQ-QMT-24")
def test_ordinary_pytest_markers_are_not_trace_links():
    source = ExtractRequest(
        '@pytest.mark.other("REQ-SVC-01")\n@pytest.mark.skip(reason="later")\n'
        '@pytest.mark.verifies("REQ-SVC-01")\nasync def test_key(): pass',
        "tests/unit/test_key.py",
        "automated_test",
        ("unit",),
        ("verifies",),
        ("verifies",),
    )
    found = adapt(pytest_tests.extract(source), source)
    assert [(link.marker, link.dst) for link in found.links] == [("verifies", "REQ-SVC-01")]
    assert found.items[0].runs_as == (("tests.unit.test_key", "test_key"),)
    assert not found.findings


@pytest.mark.verifies("REQ-QMT-12", "REQ-QMT-24")
@pytest.mark.parametrize("language", [None, "python"])
def test_missing_python_provider_refuses_before_writes(tmp_path, language):
    from qmstrace.core.errors import ProviderUnavailable
    from qmstrace.workspace._setup import initialize

    with pytest.raises(ProviderUnavailable, match="python-module"):
        initialize(tmp_path, load_config=lambda _: None, catalog=Catalog([]), language=language)
    assert not list(tmp_path.iterdir())
