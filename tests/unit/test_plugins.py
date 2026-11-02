"""The installed manifest is data; only selected, admitted handlers may execute."""

from __future__ import annotations

import importlib.metadata as metadata
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.findings import fix_stray
from qmstrace.plugin_api.v1 import (
    Diagnostic,
    Extraction,
    ExtractRequest,
    Item,
    Link,
    Stray,
    text_digest,
)
from qmstrace.plugins.adapter import adapt
from qmstrace.plugins.catalog import Catalog, PluginFault
from qmstrace.workspace import Workspace

MANIFEST = """manifest = 1
api = 1
[extractors.fixture]
module = "fixture_plugin.handler"
ids = "derived"
links = "named"
identity = "ID: fixture path"
"""
HANDLER = """from qmstrace.plugin_api.v1 import Extraction, Item, text_digest

def extract(request):
    return Extraction(items=(Item(request.path, request.item_type, request.path, 1,
                                  "fixture", text_digest(request.text)),))

def form(marker, target):
    return marker + ": " + target
"""


def distribution(
    tmp_path,
    monkeypatch,
    manifest=MANIFEST,
    handler=HANDLER,
    *,
    init="",
    name="fixture-provider",
    version="1.0",
    requirement="qmstrace>=0.4.0.dev0",
):
    package = tmp_path / "fixture_plugin"
    package.mkdir(exist_ok=True)
    (package / "__init__.py").write_text(init)
    (package / "plugin.toml").write_text(manifest)
    (package / "handler.py").write_text(handler)
    info = tmp_path / (name.replace("-", "_") + "-1.0.dist-info")
    info.mkdir(exist_ok=True)
    (info / "METADATA").write_text(
        f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\nRequires-Dist: {requirement}\n"
    )
    (info / "entry_points.txt").write_text("[qmstrace.extractors]\nfixture = fixture_plugin\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "fixture_plugin", raising=False)
    monkeypatch.delitem(sys.modules, "fixture_plugin.handler", raising=False)
    return metadata.Distribution.at(info)


def config(catalog):
    starter = Path("src/qmstrace/assets/starter.toml").read_text()
    items = '\n[items.component]\nextractor = "fixture"\nfiles = ["*.txt"]\n'
    return catalog.configuration(
        (starter + items).replace("__SUBJECT__", "demo").replace("__KEY__", "DEMO")
    )


@pytest.mark.verifies("REQ-QMT-24", "REQ-QMT-25", "DSN-QMT-17")
def test_discovery_and_inspection_never_import(tmp_path, monkeypatch):
    dist = distribution(tmp_path, monkeypatch, init='raise RuntimeError("MUST NOT IMPORT")\n')
    catalog = Catalog([dist])
    assert catalog.providers[0].problems == ()
    assert "fixture_plugin" not in sys.modules
    monkeypatch.setattr(metadata, "distributions", lambda: [dist])
    result = CliRunner().invoke(app, ["-C", str(tmp_path), "plugins", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["providers"][0]["compatible"]
    from jsonschema import Draft202012Validator

    schema = json.loads(Path("src/qmstrace/assets/cli.schema.json").read_text())
    Draft202012Validator(schema).validate(json.loads(result.output))
    assert "fixture_plugin" not in sys.modules
    cfg = config(catalog)
    with pytest.raises(PluginFault, match=r"fixture-provider.*fixture"):
        catalog.extractor("fixture")("x.txt", "text", cfg.item_types["component"], cfg)


@pytest.mark.verifies("REQ-QMT-24", "REQ-QMT-26", "DSN-QMT-17")
def test_new_provider_needs_no_host_registration_and_tracks_only_use(tmp_path, monkeypatch):
    catalog = Catalog([distribution(tmp_path, monkeypatch)])
    cfg = config(catalog)
    assert catalog.toolchain()["providers"] == []
    extract = catalog.extractor("fixture")
    first = extract("x.txt", "text", cfg.item_types["component"], cfg)
    assert first == extract("x.txt", "text", cfg.item_types["component"], cfg)
    assert first.items[0].id == "x.txt"
    assert catalog.form("fixture")("Implements", "DSN-DEMO-01") == "Implements: DSN-DEMO-01"
    assert catalog.toolchain()["providers"][0]["version"] == "1.0"
    assert catalog.toolchain() == catalog.toolchain()
    with pytest.raises(TypeError):
        catalog.descriptors["other"] = catalog.descriptors["fixture"]
    # Core cannot discover installed packages implicitly.
    with pytest.raises(CouldNotJudge):
        TraceConfig.parse(
            '[schema]\nversion=1\nproject="DEMO"\n[schema.item_types.component]\n[items.component]\nextractor="fixture"\nfiles=["*.txt"]'
        )


@pytest.mark.verifies("REQ-QMT-24", "REQ-QMT-25")
@pytest.mark.parametrize(
    "manifest",
    [
        MANIFEST.replace("api = 1", "api = 99"),
        MANIFEST.replace("api = 1", "api = 2026-11-02"),
        MANIFEST.replace("manifest = 1", "manifest = 2"),
        MANIFEST.replace('ids = "derived"', 'ids = "authored"'),
        MANIFEST.replace('links = "named"', 'links = "priority"'),
        MANIFEST.replace("fixture_plugin.handler", "foreign.handler"),
        MANIFEST.replace('identity = "ID: fixture path"', "identity = 123"),
        MANIFEST.replace('identity = "ID: fixture path"', 'identity = ""'),
        MANIFEST + "unknown = true\n",
        MANIFEST.replace("[extractors.fixture]", "unknown = 1\n[extractors.fixture]"),
        MANIFEST.replace("api = 1", "api = true"),
        "bad = [",
        "manifest=1\napi=1\nextractors=[]",
    ],
)
def test_rejected_provider_is_inspectable_and_does_not_block_markdown(
    tmp_path, monkeypatch, manifest
):
    catalog = Catalog([distribution(tmp_path, monkeypatch, manifest)])
    assert catalog.providers[0].problems
    monkeypatch.setattr(
        metadata, "distributions", lambda: [distribution(tmp_path, monkeypatch, manifest)]
    )
    inspected = CliRunner().invoke(app, ["plugins", "--json"])
    assert inspected.exit_code == 0, inspected.output
    assert json.loads(inspected.output)["data"]["providers"][0]["compatible"] is False
    catalog.require("markdown")
    with pytest.raises(CouldNotJudge):
        catalog.require("fixture")
    assert "fixture_plugin" not in sys.modules


@pytest.mark.verifies("REQ-QMT-24")
@pytest.mark.parametrize(
    "requirement", ["qmstrace>=99", "qmstrace", 'qmstrace>=0.4; python_version>="3"', "other>=1"]
)
def test_distribution_host_dependency_is_admitted_before_import(tmp_path, monkeypatch, requirement):
    catalog = Catalog([distribution(tmp_path, monkeypatch, requirement=requirement)])
    with pytest.raises(CouldNotJudge):
        catalog.require("fixture")


@pytest.mark.verifies("REQ-QMT-24")
def test_duplicate_ownership_including_bundled_names_has_no_winner(tmp_path, monkeypatch):
    one = distribution(tmp_path, monkeypatch)
    two = distribution(tmp_path, monkeypatch, name="second-provider")
    catalog = Catalog([two, one])
    with pytest.raises(CouldNotJudge, match="ambiguous"):
        catalog.require("fixture")
    duplicate = distribution(
        tmp_path, monkeypatch, MANIFEST.replace("extractors.fixture", "extractors.markdown")
    )
    with pytest.raises(CouldNotJudge, match="ambiguous"):
        Catalog([duplicate]).require("markdown")


@pytest.mark.verifies("REQ-QMT-24")
@pytest.mark.parametrize(
    "handler",
    [
        "def extract(request): return None\n",
        HANDLER.replace(
            "return Extraction(items=",
            'raise RuntimeError("failure")\n    return Extraction(items=',
        ),
        HANDLER.replace(
            "return Extraction(items=", "raise SystemExit(0)\n    return Extraction(items="
        ),
        HANDLER.replace("return Extraction(items=", "return None\n    return Extraction(items="),
        HANDLER.replace(
            "request.path, request.item_type, request.path, 1",
            'request.path, request.item_type, "/machine/path", 1',
        ),
    ],
)
def test_faults_cannot_be_successful_empty_results(tmp_path, monkeypatch, handler):
    catalog = Catalog([distribution(tmp_path, monkeypatch, handler=handler)])
    cfg = config(catalog)
    with pytest.raises(PluginFault, match="fixture-provider"):
        catalog.extractor("fixture")("x.txt", "text", cfg.item_types["component"], cfg)


@pytest.mark.verifies("REQ-QMT-24")
def test_empty_extraction_is_valid_but_invalid_form_is_a_fault(tmp_path, monkeypatch):
    handler = (
        "from qmstrace.plugin_api.v1 import Extraction\n"
        "def extract(request): return Extraction()\n"
        "def form(marker,target): return None\n"
    )
    catalog = Catalog([distribution(tmp_path, monkeypatch, handler=handler)])
    cfg = config(catalog)
    assert catalog.extractor("fixture")("x.txt", "", cfg.item_types["component"], cfg).items == ()
    with pytest.raises(PluginFault):
        catalog.form("fixture")("Implements", "DSN-DEMO-01")


@pytest.mark.verifies("REQ-QMT-24")
def test_public_contract_rejects_nested_mutability_and_invalid_values():
    request = ExtractRequest(
        "text", "x.txt", "component", ("unit",), ("Implements",), ("Implements",)
    )
    item = Item("x.txt", "component", "x.txt", 1, "x", text_digest("text"))
    good = Extraction(
        items=(item,), links=(Link("x.txt", "DSN-DEMO-01", "Implements", "x.txt", 1),)
    )
    assert adapt(good, request).items[0].digest == item.digest
    bad = [
        None,
        Extraction(items=[item]),
        Extraction(items=(replace(item, line=True),)),
        Extraction(items=(replace(item, fields={"a": "b"}),)),
        Extraction(items=(replace(item, fields=(("a", "b"), ("a", "c"))),)),
        Extraction(items=(replace(item, runs_as=(("one",),)),)),
        Extraction(items=(replace(item, level="unknown"),)),
        Extraction(items=(replace(item, digest="bad"),)),
        Extraction(items=(replace(item, type="other"),)),
        Extraction(items=(replace(item, line=0),)),
        replace(good, links=(replace(good.links[0], src="absent"),)),
        replace(good, links=(replace(good.links[0], marker="absent"),)),
        replace(good, links=(replace(good.links[0], dst="not-an-id"),)),
        Extraction(diagnostics=(Diagnostic("wrong", "x.txt", 1, "what", "fix"),)),
        Extraction(strays=(Stray("Implements", ("bad",), "x.txt", 1, "fix"),)),
        Extraction(strays=(Stray("unknown", ("DSN-DEMO-01",), "x.txt", 1, "fix"),)),
        Extraction(strays=(Stray("Implements", ("DSN-DEMO-01",), "x.txt", 1, ""),)),
    ]
    for value in bad:
        with pytest.raises(ValueError):
            adapt(value, request)
    stray = Stray("Implements", ("DSN-DEMO-01",), "x.txt", 1, "move at {location}")
    found = adapt(Extraction(strays=(stray,)), request).qualified("demo", "../demo", frozenset())
    assert fix_stray(found.strays[0]) == "move at ../demo/x.txt:1"


@pytest.mark.verifies("REQ-QMT-12", "REQ-QMT-24")
def test_missing_csharp_provider_refuses_before_init_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(metadata, "distributions", lambda: [])
    with pytest.raises(CouldNotJudge, match="csharp-file"):
        Workspace.initialize(tmp_path, language="csharp")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.verifies("REQ-QMT-24", "REQ-QMT-26")
def test_workspace_json_identifies_used_csharp_and_fault_names_provider(tmp_path, monkeypatch):
    (tmp_path / "qmstrace.toml").write_text(
        (
            Path("src/qmstrace/assets/starter.toml").read_text()
            + "\n"
            + Path("src/qmstrace/assets/items-csharp.toml").read_text()
        )
        .replace("__SUBJECT__", "demo")
        .replace("__KEY__", "DEMO")
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Key.cs").write_text("public class Key {}")
    result = CliRunner().invoke(app, ["-C", str(tmp_path), "status", "--json"])
    assert result.exit_code == 0, result.output
    toolchain = json.loads(result.output)["data"]["toolchain"]
    assert toolchain["providers"][0]["distribution"] == "qmstrace-lang-csharp"
    assert toolchain["providers"][0]["parser_dependencies"]["tree-sitter"]
    assert str(tmp_path) not in json.dumps(toolchain)
    from qmstrace_lang_csharp import component

    monkeypatch.setattr(component, "extract", lambda request: None)
    failed = CliRunner().invoke(app, ["-C", str(tmp_path), "status", "--json"])
    assert failed.exit_code == 3
    assert "qmstrace-lang-csharp" in json.loads(failed.output)["error"]["message"]


@pytest.mark.verifies("REQ-QMT-25")
def test_metadata_inspection_has_a_plain_golden(tmp_path, monkeypatch, golden):
    monkeypatch.setattr(metadata, "distributions", lambda: [])
    result = CliRunner().invoke(app, ["-C", str(tmp_path), "plugins"])
    assert result.exit_code == 0
    golden(Path(__file__).parents[1] / "cli/golden/plugins-empty.txt", result.output)


@pytest.mark.verifies("REQ-QMT-24", "REQ-QMT-26")
def test_historical_scan_uses_same_catalog_and_refuses_missing_old_capability(
    tmp_path, monkeypatch, make_repo
):
    import subprocess

    dist = distribution(tmp_path, monkeypatch)
    catalog = Catalog([dist])
    repo = tmp_path / "repo"
    repo.mkdir()
    raw = (
        (
            Path("src/qmstrace/assets/starter.toml").read_text()
            + """
[schema.baselines.all]
tag = '^baseline/1$'
covers = ['component']
subject = '*'
[items.component]
extractor = 'fixture'
files = ['*.txt']
"""
        )
        .replace("__SUBJECT__", "demo")
        .replace("__KEY__", "DEMO")
    )
    (repo / "qmstrace.toml").write_text(raw)
    (repo / "x.txt").write_text("historical")
    make_repo(repo)
    subprocess.run(["git", "tag", "-a", "baseline/1", "-m", "fixture"], cwd=repo, check=True)
    (repo / "x.txt").write_text("current")
    opened = Workspace.open(repo, catalog=catalog)
    view = opened.assessment()
    historical = view.baseline_state.baselines[0].snapshot.items
    assert next(i for i in historical if i.id == "x.txt").digest == text_digest("historical")
    assert view.graph.nodes["x.txt"].item.digest == text_digest("current")
    assert view.toolchain["extractors"] == ["fixture", "markdown"]
    # Only the tagged configuration requires the plugin now. Its absence still refuses.
    (repo / "qmstrace.toml").write_text(
        raw.replace("extractor = 'fixture'", "extractor = 'python-module'")
    )
    with pytest.raises(CouldNotJudge, match="Historical trace data"):
        Workspace.open(
            repo, catalog=Catalog([metadata.distribution("qmstrace-lang-python")])
        ).assessment()


@pytest.mark.verifies("REQ-QMT-24")
def test_editable_manifest_is_read_without_import(tmp_path, monkeypatch):
    dist = distribution(tmp_path, monkeypatch, init='raise AssertionError("executed")')
    package = tmp_path / "fixture_plugin"
    source = tmp_path / "source"
    source.mkdir()
    package.rename(source / "fixture_plugin")
    monkeypatch.syspath_prepend(str(source))
    info = tmp_path / "fixture_provider-1.0.dist-info"
    (info / "direct_url.json").write_text(
        json.dumps({"url": source.as_uri(), "dir_info": {"editable": True}})
    )
    catalog = Catalog([dist])
    catalog.require("fixture")
    assert "fixture_plugin" not in sys.modules
    (info / "direct_url.json").write_text("{}")
    assert Catalog([dist]).providers[0].problems


@pytest.mark.verifies("REQ-QMT-24")
def test_one_catalog_is_shared_with_siblings_and_project_members(project, monkeypatch):
    import qmstrace.workspace._project as whole
    import qmstrace.workspace._workspace as local
    from qmstrace.workspace import _discovery

    seen = []
    original = _discovery._configuration

    def configuration(root, tree, catalog=None):
        seen.append(catalog)
        return original(root, tree, catalog)

    monkeypatch.setattr(local, "_configuration", configuration)
    from qmstrace.workspace import _sources

    monkeypatch.setattr(_sources, "_configuration", configuration)
    opened = Workspace.open(project / "service")
    opened.assessment()
    assert seen and all(c is opened.catalog for c in seen)
    seen.clear()
    monkeypatch.setattr(whole, "_configuration", configuration)
    Workspace.project(project / "ledger")
    assert len(seen) >= 2 and len({id(c) for c in seen}) == 1


@pytest.mark.verifies("REQ-QMT-24", "REQ-QMT-25")
@pytest.mark.parametrize(
    "direct",
    [
        [],
        None,
        {"dir_info": []},
        {"dir_info": {"editable": True}, "url": []},
        {"dir_info": {"editable": True}, "url": "https://example.invalid/source"},
    ],
)
def test_malformed_editable_metadata_does_not_block_other_extractors(tmp_path, monkeypatch, direct):
    dist = distribution(tmp_path, monkeypatch)
    (tmp_path / "fixture_plugin/plugin.toml").unlink()
    (tmp_path / "fixture_provider-1.0.dist-info/direct_url.json").write_text(json.dumps(direct))
    catalog = Catalog([dist])
    assert catalog.providers[0].problems
    monkeypatch.setattr(metadata, "distributions", lambda: [dist])
    inspected = CliRunner().invoke(app, ["plugins", "--json"])
    assert inspected.exit_code == 0, inspected.output
    assert json.loads(inspected.output)["data"]["providers"][0]["compatible"] is False
    catalog.require("markdown")


@pytest.mark.verifies("REQ-QMT-02", "REQ-QMT-24", "DSN-QMT-17")
def test_adapter_preserves_duplicate_declarations_for_host_validation(service):
    from qmstrace.core.graph import TraceGraph

    source = ExtractRequest("text", "src/key.py", "component")
    first = Item("src/key.py", "component", "src/key.py", 1, "first", text_digest("first"))
    second = replace(first, line=4, title="second", digest=text_digest("second"))
    found = adapt(Extraction(items=(first, second)), source)
    assert [(i.line, i.title, i.digest) for i in found.items] == [
        (1, "first", first.digest),
        (4, "second", second.digest),
    ]
    _, findings = TraceGraph.build(service, [found])
    assert [f.code for f in findings] == ["V01"]
