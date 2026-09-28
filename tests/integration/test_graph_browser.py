"""The browser contains exactly the engine's reach, findings and evidence."""

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.render.graph import document, projection
from qmstrace.workspace import Workspace


@pytest.mark.verifies("DSN-QMT-13")
def test_reach_and_evidence_match_shared_core(project: Path) -> None:
    for repo in ("service", "client", "solo"):
        a = Workspace.open(project / repo).assessment()
        data = projection(a)
        ids = [n["id"] for n in data["nodes"]]
        assert ids == sorted(a.graph.nodes)
        for i, key in enumerate(ids):
            for direction in ("forward", "backward"):
                expected = {
                    k: s.distance
                    for k, s in getattr(a.graph, direction)([key]).steps.items()
                    if k != key
                }
                actual = {ids[j]: d for j, d in data["reach"][i][direction]}
                assert actual == expected
        assert len(data["findings"]) == len(a.violations) + len(a.gaps) + len(a.suspects)
        assert all(n.text in data["evidence"] for n in a.notices)
        assert {(ids[k["src"]], ids[k["dst"]], k["marker"]) for k in data["links"]} == {
            (k.src, k.dst, k.marker) for k in a.graph.links
        }


@pytest.mark.verifies("DSN-QMT-13", "REQ-QMT-16")
def test_standalone_html_escapes_hostile_text_and_is_deterministic(project: Path) -> None:
    a = Workspace.open(project / "service").assessment()
    hostile = '</script><script>alert("bad")</script>&\u2028'
    nodes = dict(a.graph.nodes)
    key = next(iter(nodes))
    nodes[key] = replace(nodes[key], title=hostile)
    a = replace(a, graph=replace(a.graph, nodes=nodes))
    html = document(a)
    assert html == document(a)
    assert hostile not in html
    payload = re.search(
        r'<script id="assessment" type="application/json">(.*?)</script>', html, re.S
    )[1]
    assert next(n["title"] for n in json.loads(payload)["nodes"] if n["id"] == key) == hostile
    assert "connect-src 'none'" in html
    assert not re.search(r"<script[^>]+src=", html)
    assert "innerHTML" not in Path("src/qmstrace/assets/graph.js").read_text()


@pytest.mark.verifies("REQ-QMT-16")
def test_graph_cli_and_paths(project: Path, golden) -> None:
    root = project / "service"
    runner = CliRunner()
    out = root / "trace.html"
    args = ["-C", str(root), "graph", "REQ-SVC-01", "--out", "trace.html"]
    first = runner.invoke(app, args)
    assert first.exit_code == 0, first.output
    golden(Path("tests/cli/golden/graph-service.txt"), first.output)
    original = out.read_bytes()
    refused = runner.invoke(app, args)
    assert refused.exit_code == 2
    assert out.read_bytes() == original
    out.unlink()
    second = runner.invoke(app, ["graph", "REQ-SVC-01", "--out", "trace.html", "-C", str(root)])
    assert second.output == first.output and second.exit_code == 0
    assert out.read_bytes() == original
    missing = runner.invoke(app, ["graph", "REQ-SVC-99", "--out", "unseen.html", "-C", str(root)])
    assert missing.exit_code == 2 and not (root / "unseen.html").exists()
    sub = runner.invoke(app, ["graph", "--out", "sub.html", "-C", str(root / "src")])
    assert sub.exit_code == 0, sub.output
    assert (root / "src/sub.html").exists()
    bad = runner.invoke(app, ["graph", "--out", "no-dir/sub.html", "-C", str(root)])
    assert bad.exit_code == 2


def test_suspect_badges_and_historical_only_reasons(project: Path, embed) -> None:
    import subprocess

    root = project / "service"
    config = root / "qmstrace.toml"
    config.write_text(
        embed(config.read_text(), (project / "ledger/qmstrace.schema.toml").read_text())
    )
    for args in [
        ("add", "-A"),
        ("commit", "-qm", "embedded"),
        ("tag", "-a", "baseline/service/requirements/1", "-m", "baseline"),
    ]:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    req = root / "docs/req/service-srs.md"
    req.write_text(req.read_text().replace("A call carries a key", "A call requires a fresh key"))
    design = root / "docs/design/service-design.md"
    design.write_text(design.read_text().replace("Satisfies: REQ-SVC-01", "Status: withdrawn"))
    a = Workspace.open(root).assessment()
    data = projection(a)
    assert set(n["type"] for n in data["nodes"]) <= set(data["types"])
    d = next(n for n in data["nodes"] if n["id"] == "DSN-SVC-01")
    assert "withdrawn" in d["badges"] and "suspect — needs review" in d["badges"]
    r = next(n for n in data["nodes"] if n["id"] == "REQ-SVC-01")
    assert r["badges"] == ["frozen", "changed"]
    finding = next(f for f in data["findings"] if f["code"] == "S01" and f["item"] == "DSN-SVC-01")
    assert "historical-only" in finding["what"] and "edited" in finding["what"]
    assert "baseline/service/requirements/1" in finding["what"]
    assert not any(
        data["nodes"][e["src"]]["id"] == "DSN-SVC-01"
        and data["nodes"][e["dst"]]["id"] == "REQ-SVC-01"
        for e in data["links"]
    )
