"""The import matrix — a layering rule that lives only in a document is already broken.

The load-bearing claims, each pinned by a test:

1. Each package imports only what `docs/structure/codebase-blueprint.md` § 6 allows — and
   every import is absolute, so the check above cannot be walked around.
2. Nothing imports `click`: the framework vendors it privately, and it is not installed.
3. Package initializers are empty, except the config, judge, graph, setup, Markdown and text
   compatibility exports, plus the workspace and CLI compatibility facades.
4. An extractor takes text and never touches the file system: the same extractor reads the
   working tree, a tree at a baseline tag and a sibling.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).parents[2] / "src" / "qmstrace"

# rows may import columns — third-party and first-party only; the standard library is free
ALLOWED: dict[str, set[str]] = {
    "core": {"qmstrace.core"},
    "extract": {
        "qmstrace.core",
        "qmstrace.extract",
        "defusedxml",
        "tree_sitter",
        "tree_sitter_c_sharp",
    },
    "infra": {"qmstrace.core", "qmstrace.infra"},
    "render": {"qmstrace.core", "qmstrace.render"},
    "workspace": {"qmstrace.core", "qmstrace.extract", "qmstrace.infra", "qmstrace.workspace"},
    "cli": {"qmstrace", "qmstrace.core", "qmstrace.render", "qmstrace.workspace", "typer"},
}
FIRST_OR_THIRD_PARTY = (
    "qmstrace",
    "typer",
    "click",
    "defusedxml",
    "pytest",
    "tree_sitter",
    "tree_sitter_c_sharp",
)


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                candidate = f"{node.module}.{alias.name}"
                relative = candidate.removeprefix("qmstrace.").replace(".", "/")
                is_module = candidate.startswith("qmstrace.") and (
                    (SRC / f"{relative}.py").is_file() or (SRC / relative).is_dir()
                )
                found.add(candidate if is_module else node.module)
    return {name for name in found if name.split(".")[0] in FIRST_OR_THIRD_PARTY}


def _area(path: Path) -> str:
    relative = path.relative_to(SRC)
    return relative.parts[0] if len(relative.parts) > 1 else relative.stem


def _modules() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if _area(p) in ALLOWED)


@pytest.mark.parametrize("path", _modules(), ids=lambda p: str(p.relative_to(SRC)))
def test_a_module_imports_only_what_its_layer_may(path: Path) -> None:
    allowed = ALLOWED[_area(path)]
    for name in _imports(path):
        permitted = any(name == ok or name.startswith(ok + ".") for ok in allowed)
        assert permitted, (
            f"{path.relative_to(SRC)} imports {name}; "
            f"{_area(path)} may import only {sorted(allowed)}"
        )


def test_every_import_is_absolute() -> None:
    relative = [
        f"{path.relative_to(SRC)}:{node.lineno}"
        for path in SRC.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom) and node.level
    ]
    assert not relative, f"relative imports hide a layer from the matrix: {relative}"


def test_nothing_imports_click() -> None:
    offenders = [str(p.relative_to(SRC)) for p in SRC.rglob("*.py") if "click" in _imports(p)]
    assert not offenders, (
        f"{offenders} import click — the framework vendors it; it is not installed"
    )


CONFIG_IMPORTS: dict[str, set[str]] = {
    "_schema": set(),
    "_toml": {"qmstrace.core.errors"},
    "_copy": set(),
    "_sections": {
        "qmstrace.core.config._schema",
        "qmstrace.core.config._toml",
        "qmstrace.core.errors",
    },
    "_parse": {
        "qmstrace.core.config._schema",
        "qmstrace.core.config._toml",
        "qmstrace.core.config._copy",
        "qmstrace.core.config._sections",
        "qmstrace.core.errors",
    },
}


JUDGE_IMPORTS: dict[str, set[str]] = {
    "_coverage": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.graph",
        "qmstrace.core.model",
    },
    "_baselines": {
        "qmstrace.core.findings",
        "qmstrace.core.baselines",
        "qmstrace.core.config",
        "qmstrace.core.errors",
        "qmstrace.core.model",
    },
    "_suspects": {"qmstrace.core.baselines", "qmstrace.core.graph"},
}
GRAPH_IMPORTS: dict[str, set[str]] = {
    "_nodes": {"qmstrace.core.model"},
    "_validation": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.core.graph._nodes",
    },
    "_graph": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.core.graph._nodes",
        "qmstrace.core.graph._validation",
    },
}
SETUP_IMPORTS: dict[str, set[str]] = {
    "_guide": {"qmstrace.core.config", "qmstrace.core.errors"},
    "_pytest": {"qmstrace.core.errors"},
    "_schema_copy": {"qmstrace.core.config", "qmstrace.core.errors"},
}
MARKDOWN_IMPORTS: dict[str, set[str]] = {
    "_headings": {"qmstrace.core.config", "qmstrace.core.model"},
    "_tables": {"qmstrace.core.model", "qmstrace.extract.fields"},
    "_extract": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.extract.fields",
        "qmstrace.extract.markdown._headings",
        "qmstrace.extract.markdown._tables",
    },
}
PYTHON_IMPORTS: dict[str, set[str]] = {
    "module": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.extract.fields",
    },
    "pytest_tests": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.core.results",
    },
}
CSHARP_IMPORTS: dict[str, set[str]] = {
    "_syntax": {"tree_sitter", "tree_sitter_c_sharp"},
    "component": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.extract.csharp._syntax",
        "qmstrace.extract.fields",
    },
    "xunit": {
        "qmstrace.core.findings",
        "qmstrace.core.config",
        "qmstrace.core.model",
        "qmstrace.extract.csharp._syntax",
    },
}
PYTHON_COMPATIBILITY = {
    "python_module": {"qmstrace.extract.python.module": {"extract", "form"}},
    "pytest_tests": {
        "qmstrace.extract.python.pytest_tests": {"extract", "form", "report_identity"}
    },
}
TEXT_IMPORTS: dict[str, set[str]] = {
    "_schema": {"qmstrace.core.setup", "qmstrace.core.config"},
    "_status": {
        "qmstrace.core.model",
        "qmstrace.core.assessment",
        "qmstrace.render._evidence",
        "qmstrace.render._presentation",
        "qmstrace.core.findings",
        "qmstrace.core.config",
    },
    "_results": {
        "qmstrace.render._evidence",
        "qmstrace.core.results",
        "qmstrace.render._presentation",
    },
    "_checks": {
        "qmstrace.core.model",
        "qmstrace.core.assessment",
        "qmstrace.core.baselines",
        "qmstrace.render._evidence",
        "qmstrace.render._presentation",
        "qmstrace.core.findings",
    },
    "_walks": {
        "qmstrace.core.assessment",
        "qmstrace.core.graph",
        "qmstrace.render._evidence",
        "qmstrace.render._presentation",
        "qmstrace.core.config",
    },
}
RENDER_SHARED_IMPORTS: dict[str, set[str]] = {
    "_presentation": {"qmstrace.core.graph", "qmstrace.core.model"},
    "_evidence": {
        "qmstrace.core.baselines",
        "qmstrace.render._presentation",
        "qmstrace.core.assessment",
        "qmstrace.core.config",
    },
}
PACKAGE_IMPORTS = {
    "config": CONFIG_IMPORTS,
    "judge": JUDGE_IMPORTS,
    "graph": GRAPH_IMPORTS,
    "setup": SETUP_IMPORTS,
    "markdown": MARKDOWN_IMPORTS,
    "python": PYTHON_IMPORTS,
    "csharp": CSHARP_IMPORTS,
    "text": TEXT_IMPORTS,
}
PACKAGE_AREAS = {
    name: "extract"
    if name in {"markdown", "python", "csharp"}
    else "render"
    if name == "text"
    else "core"
    for name in PACKAGE_IMPORTS
}
EXPORTS: dict[str, dict[str, set[str]]] = {
    "text": {
        "qmstrace.render._evidence": {"evidence"},
        "_checks": {"VIOLATION_HEADING", "check", "PROJECT_GAP_HEADING", "ledger_check"},
        "_results": {"results"},
        "_schema": {"schema_copies", "rules"},
        "_status": {"status", "VERIFY_BY", "CATEGORY", "LISTED", "TESTED"},
        "_walks": {"impact", "ledger_thread", "thread", "ledger_impact"},
    },
    "markdown": {"_extract": {"CHANGE", "extract", "form"}},
    "setup": {
        "_guide": {
            "BEGIN",
            "END",
            "SKILL_FILE",
            "CLAUDE_LINK",
            "CLAUDE_LINK_TARGET",
            "LEGACY_SKILL",
            "stanza",
            "guide",
        },
        "_pytest": {"MARKER", "pytest_section", "register_marker"},
        "_schema_copy": {
            "Held",
            "Copied",
            "ledger_itself",
            "before_copy",
            "held_schema",
            "schema_block",
            "copy_schema",
        },
    },
    "config": {
        "_copy": {"COPY_BEGIN", "COPY_END", "marked", "schema_digest", "structural"},
        "_parse": {"TraceConfig"},
        "_schema": {
            "EXTRACTORS",
            "BaselineScope",
            "ChangeRequests",
            "CoverageRule",
            "ExternalSource",
            "ItemType",
            "LinkType",
            "SchemaForm",
            "Subject",
            "Tables",
        },
        "_toml": {"SUPPORTED_VERSION"},
    },
    "judge": {
        "_coverage": {"Form", "Way", "coverage"},
        "_baselines": {"guard", "resolve_baselines"},
        "_suspects": {"suspects"},
    },
    "graph": {
        "_nodes": {"Home", "Node", "Surroundings"},
        "_graph": {"TraceGraph", "Direction", "Step", "Closure"},
    },
}


def _check_initializers(root: Path) -> None:
    exceptions = {f"{PACKAGE_AREAS[p]}/{p}/__init__.py": p for p in EXPORTS}
    for init in root.rglob("__init__.py"):
        if init == root / "__init__.py":
            continue  # package version
        text = init.read_text(encoding="utf-8")
        if init.relative_to(root).as_posix() == "cli/__init__.py":
            _check_exports(text, CLI_EXPORTS)
            continue
        if init.relative_to(root).as_posix() == "workspace/__init__.py":
            _check_exports(text, WORKSPACE_EXPORTS)
            continue
        package = exceptions.get(init.relative_to(root).as_posix())
        if package is None:
            assert not text.strip(), f"{init.relative_to(root)} is not empty"
            continue
        expected = {
            (
                owner
                if owner.startswith("qmstrace.")
                else f"qmstrace.{PACKAGE_AREAS[package]}.{package}.{owner}"
            ): names
            for owner, names in EXPORTS[package].items()
        }
        _check_exports(text, expected)


def _check_exports(text: str, expected: dict[str, set[str]]) -> None:
    found: dict[str, set[str]] = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            assert isinstance(node.value.value, str)  # documentation only
            continue
        assert isinstance(node, ast.ImportFrom), "exports must be direct imports"
        assert node.level == 0 and node.module in expected
        for alias in node.names:
            assert alias.name in expected[node.module] and alias.asname == alias.name
            names = found.setdefault(node.module, set())
            assert alias.name not in names, "duplicate compatibility export"
            names.add(alias.name)
    assert found == expected, "compatibility exports must preserve the exact interface"


def test_a_subpackage_init_holds_no_code_except_approved_exports() -> None:
    _check_initializers(SRC)


@pytest.mark.parametrize(
    ("relative", "source"),
    [
        ("cli/__init__.py", "from qmstrace.cli._app import *\n"),
        ("cli/__init__.py", "from qmstrace.cli._options import _directory as _directory\n"),
        ("cli/nested/__init__.py", "import typer\n"),
        ("workspace/__init__.py", "from qmstrace.workspace._workspace import *\n"),
        ("workspace/__init__.py", "from qmstrace.workspace._scanning import _scan as _scan\n"),
        ("workspace/nested/__init__.py", "import os\n"),
        ("render/text/__init__.py", "from qmstrace.render.text._status import *\n"),
        ("render/text/__init__.py", "from qmstrace.render._evidence import _unread as _unread\n"),
        ("render/text/deep/__init__.py", "import os\n"),
        ("core/deep/nested/__init__.py", "import os\n"),
        (
            "extract/python/__init__.py",
            "from qmstrace.extract.python.module import extract as extract\n",
        ),
        ("extract/markdown/__init__.py", ""),
        ("extract/markdown/__init__.py", "from qmstrace.extract.markdown._extract import *\n"),
        (
            "extract/markdown/__init__.py",
            "from qmstrace.extract.markdown._headings import _heading as _heading\n",
        ),
        ("extract/markdown/nested/__init__.py", "import os\n"),
        ("core/config/__init__.py", "value = 1\n"),
        ("core/config/__init__.py", "from qmstrace.core.config._schema import *\n"),
        ("core/config/__init__.py", "from qmstrace.workspace import Workspace as Workspace\n"),
        ("core/judge/__init__.py", "from qmstrace.core.judge._coverage import _fix as _fix\n"),
        ("core/graph/__init__.py", "from qmstrace.core.graph._graph import TraceGraph\n"),
        ("core/graph/__init__.py", ""),
        (
            "core/setup/__init__.py",
            "from qmstrace.core.setup._guide import _PRODUCT_LINES as _PRODUCT_LINES\n",
        ),
        ("core/judge/deep/__init__.py", "from qmstrace.core.judge import guard as guard\n"),
    ],
)
def test_the_initializer_gate_rejects_nested_code_and_broad_exports(
    tmp_path: Path, relative: str, source: str
) -> None:
    file = tmp_path / relative
    file.parent.mkdir(parents=True)
    file.write_text(source, encoding="utf-8")
    with pytest.raises(AssertionError):
        _check_initializers(tmp_path)


def _check_dependencies(package: str, path: Path) -> None:
    assert _imports(path) <= PACKAGE_IMPORTS[package][path.stem], (
        f"{package}/{path.name} reaches outside its dependencies: {_imports(path)}"
    )


@pytest.mark.parametrize("name", PACKAGE_IMPORTS)
def test_package_dependencies_are_one_way_and_callers_use_the_public_interface(name: str) -> None:
    package = SRC / PACKAGE_AREAS[name] / name
    assert {p.stem for p in package.glob("*.py") if p.stem != "__init__"} == set(
        PACKAGE_IMPORTS[name]
    )
    for path in package.glob("*.py"):
        if path.name != "__init__.py":
            _check_dependencies(name, path)
    # The language packages expose concrete owner modules; the others only their facade.
    for path in SRC.rglob("*.py"):
        if name not in ("python", "csharp") and path.parent != package:
            assert not any(
                n.startswith(f"qmstrace.{PACKAGE_AREAS[name]}.{name}.") for n in _imports(path)
            )


@pytest.mark.parametrize(
    ("package", "module", "source"),
    [
        ("text", "_status", "from qmstrace.render.text import check"),
        ("text", "_checks", "from qmstrace.render.text import _status"),
        ("text", "_results", "from qmstrace.render import graph"),
        ("text", "_walks", "from qmstrace import workspace"),
        ("python", "module", "from qmstrace.extract import python_module"),
        ("python", "pytest_tests", "from qmstrace.extract.python import module"),
        ("python", "module", "from qmstrace.extract.python.pytest_tests import report_identity"),
        ("python", "pytest_tests", "import pytest"),
        ("markdown", "_headings", "from qmstrace.extract.markdown import extract"),
        ("markdown", "_tables", "from qmstrace.extract.markdown import _extract"),
        ("markdown", "_extract", "from qmstrace.extract import base"),
        ("markdown", "_headings", "from qmstrace.extract.markdown._tables import _cells"),
        ("config", "_schema", "from qmstrace.core.config import TraceConfig"),
        ("setup", "_guide", "from qmstrace.core.setup import stanza"),
        ("setup", "_pytest", "from qmstrace.core.setup import _schema_copy"),
        ("setup", "_schema_copy", "from qmstrace.core.setup._guide import guide"),
        ("judge", "_coverage", "from qmstrace.core.judge import guard"),
        ("judge", "_baselines", "from qmstrace.core.judge import _suspects"),
        ("graph", "_nodes", "from qmstrace.core.graph._graph import TraceGraph"),
        ("graph", "_validation", "from qmstrace.core.graph import _graph"),
        ("graph", "_graph", "from qmstrace.core import judge"),
        (
            "graph",
            "_nodes",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
            "    from qmstrace.core.graph import TraceGraph",
        ),
    ],
)
def test_the_dependency_gate_rejects_back_edges(
    tmp_path: Path, package: str, module: str, source: str
) -> None:
    file = tmp_path / f"{module}.py"
    file.write_text(source + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        _check_dependencies(package, file)


# what reaching the file system looks like, in the source of an extractor
_FILE_SYSTEM_MODULES = {"os", "io", "pathlib", "shutil", "subprocess", "glob", "tempfile"}
_FILE_SYSTEM_CALLS = {"open", "read_text", "read_bytes", "write_text", "write_bytes", "iterdir"}


@pytest.mark.verifies("DSN-QMT-04")
def test_an_extractor_never_touches_the_file_system() -> None:
    for path in sorted((SRC / "extract").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = {node.module.split(".")[0]}
            elif isinstance(node, ast.Name | ast.Attribute):
                names = {node.id if isinstance(node, ast.Name) else node.attr}
                names &= _FILE_SYSTEM_CALLS
            else:
                continue
            reached = names & (_FILE_SYSTEM_MODULES | _FILE_SYSTEM_CALLS)
            assert not reached, (
                f"{path.relative_to(SRC)}:{node.lineno} reaches the file system ({reached}); "
                "an extractor takes text — the tree reads files"
            )


def _check_python_callers(path: Path) -> None:
    old = {f"qmstrace.extract.{name}" for name in PYTHON_COMPATIBILITY}
    assert not (_imports(path) & old), "production callers must use extract.python owners"


def test_python_compatibility_modules_only_forward_the_supported_functions() -> None:
    for name, expected in PYTHON_COMPATIBILITY.items():
        path = SRC / "extract" / f"{name}.py"
        _check_exports(path.read_text(encoding="utf-8"), expected)
    for path in SRC.rglob("*.py"):
        _check_python_callers(path)


@pytest.mark.parametrize(
    "source",
    [
        "from qmstrace.extract.python.module import *",
        "from qmstrace.extract.python.module import _strays as _strays",
        "from qmstrace.extract.python.module import extract",
        "def extract(*args): return None",
    ],
)
def test_python_compatibility_gate_rejects_extra_exports_and_wrappers(source: str) -> None:
    with pytest.raises(AssertionError):
        _check_exports(source, PYTHON_COMPATIBILITY["python_module"])


@pytest.mark.parametrize(
    "source",
    [
        "from qmstrace.extract import python_module",
        "from qmstrace.extract.pytest_tests import report_identity",
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
        "    from qmstrace.extract import pytest_tests",
    ],
)
def test_python_callers_gate_rejects_legacy_imports(tmp_path: Path, source: str) -> None:
    path = tmp_path / "caller.py"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(AssertionError):
        _check_python_callers(path)


def _check_shared_render_dependencies(path: Path) -> None:
    assert _imports(path) <= RENDER_SHARED_IMPORTS[path.stem]


def test_shared_rendering_never_imports_a_command_renderer() -> None:
    for name in RENDER_SHARED_IMPORTS:
        _check_shared_render_dependencies(SRC / "render" / f"{name}.py")
    assert "qmstrace.render.text" not in _imports(SRC / "render/graph.py")
    assert "qmstrace.render._evidence" in _imports(SRC / "render/graph.py")


@pytest.mark.parametrize(
    ("owner", "source"),
    [
        ("_evidence", "from qmstrace.render.text import status"),
        ("_evidence", "from qmstrace.render import graph"),
        ("_presentation", "from qmstrace.render import _evidence"),
        (
            "_presentation",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
            "    from qmstrace.render.text import check",
        ),
    ],
)
def test_shared_render_dependency_gate_rejects_back_edges(
    tmp_path: Path, owner: str, source: str
) -> None:
    path = tmp_path / f"{owner}.py"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(AssertionError):
        _check_shared_render_dependencies(path)


WORKSPACE_IMPORTS: dict[str, set[str]] = {
    "_baselines": {
        "qmstrace.core.baselines",
        "qmstrace.core.config",
        "qmstrace.core.errors",
        "qmstrace.core.findings",
        "qmstrace.core.graph",
        "qmstrace.core.judge",
        "qmstrace.core.model",
        "qmstrace.infra.git",
        "qmstrace.infra.tree",
        "qmstrace.workspace._discovery",
        "qmstrace.workspace._scanning",
    },
    "_discovery": {"qmstrace.core.errors", "qmstrace.core.config", "qmstrace.infra.tree"},
    "_project": {
        "qmstrace.core.assessment",
        "qmstrace.core.baselines",
        "qmstrace.core.config",
        "qmstrace.core.errors",
        "qmstrace.core.graph",
        "qmstrace.core.judge",
        "qmstrace.core.model",
        "qmstrace.extract.base",
        "qmstrace.infra.files",
        "qmstrace.infra.git",
        "qmstrace.infra.tree",
        "qmstrace.workspace._baselines",
        "qmstrace.workspace._discovery",
        "qmstrace.workspace._scanning",
        "qmstrace.workspace._sources",
    },
    "_scanning": {
        "qmstrace.core.assessment",
        "qmstrace.core.config",
        "qmstrace.core.findings",
        "qmstrace.core.model",
        "qmstrace.extract.base",
        "qmstrace.infra.globbing",
        "qmstrace.infra.tree",
    },
    "_setup": {
        "qmstrace.core.config",
        "qmstrace.core.errors",
        "qmstrace.core.setup",
        "qmstrace.infra.files",
        "qmstrace.workspace._discovery",
    },
    "_sources": {
        "qmstrace.core.assessment",
        "qmstrace.core.baselines",
        "qmstrace.core.config",
        "qmstrace.core.errors",
        "qmstrace.core.findings",
        "qmstrace.core.model",
        "qmstrace.extract.change_requests",
        "qmstrace.infra.externals",
        "qmstrace.workspace._discovery",
        "qmstrace.workspace._scanning",
    },
    "_workspace": {
        "qmstrace.core.assessment",
        "qmstrace.core.baselines",
        "qmstrace.core.config",
        "qmstrace.core.errors",
        "qmstrace.core.graph",
        "qmstrace.core.judge",
        "qmstrace.core.model",
        "qmstrace.core.results",
        "qmstrace.core.setup",
        "qmstrace.extract.base",
        "qmstrace.extract.python.pytest_tests",
        "qmstrace.extract.reports",
        "qmstrace.infra.files",
        "qmstrace.infra.git",
        "qmstrace.infra.tree",
        "qmstrace.workspace._baselines",
        "qmstrace.workspace._discovery",
        "qmstrace.workspace._project",
        "qmstrace.workspace._scanning",
        "qmstrace.workspace._setup",
        "qmstrace.workspace._sources",
    },
}

WORKSPACE_EXPORTS = {
    "qmstrace.workspace._workspace": {"Workspace"},
    "qmstrace.workspace._discovery": {"TreeFactory", "CONFIG_FILE", "SCHEMA_FILE"},
}


def _check_workspace_dependencies(path: Path) -> None:
    assert _imports(path) <= WORKSPACE_IMPORTS[path.stem]


def test_workspace_owners_are_one_way_and_callers_use_the_facade() -> None:
    package = SRC / "workspace"
    assert {p.stem for p in package.glob("*.py") if p.stem != "__init__"} == set(WORKSPACE_IMPORTS)
    for path in package.glob("*.py"):
        if path.stem != "__init__":
            _check_workspace_dependencies(path)
    for path in SRC.rglob("*.py"):
        if path.parent != package:
            assert not any(n.startswith("qmstrace.workspace.") for n in _imports(path))


@pytest.mark.parametrize(
    ("owner", "source"),
    [
        ("_scanning", "from qmstrace.workspace import Workspace"),
        ("_sources", "from qmstrace.workspace._workspace import Workspace"),
        ("_baselines", "from qmstrace.workspace._project import project"),
        ("_project", "from qmstrace.workspace._setup import initialize"),
        ("_setup", "from qmstrace.workspace._workspace import Workspace"),
        ("_discovery", "from qmstrace.workspace._scanning import _scan"),
        ("_workspace", "from qmstrace.render import text"),
        (
            "_scanning",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
            "    from qmstrace.workspace._workspace import Workspace",
        ),
    ],
)
def test_workspace_dependency_gate_rejects_back_edges(
    tmp_path: Path, owner: str, source: str
) -> None:
    path = tmp_path / f"{owner}.py"
    path.write_text(source + "\n")
    with pytest.raises(AssertionError):
        _check_workspace_dependencies(path)


CLI_IMPORTS: dict[str, set[str]] = {
    "_app": {
        "qmstrace",
        "qmstrace.cli._ledger",
        "qmstrace.cli._local",
        "qmstrace.cli._options",
        "qmstrace.cli._outcome",
        "typer",
    },
    "_ledger": {
        "qmstrace.cli._options",
        "qmstrace.cli._outcome",
        "qmstrace.core.tables",
        "qmstrace.render.tables",
        "qmstrace.render.text",
        "qmstrace.workspace",
        "typer",
    },
    "_local": {
        "qmstrace.cli._options",
        "qmstrace.cli._outcome",
        "qmstrace.render.graph",
        "qmstrace.render.text",
        "qmstrace.workspace",
        "typer",
    },
    "_options": {"typer"},
    "_outcome": {"qmstrace.core.errors", "typer"},
}

CLI_EXPORTS = {
    "qmstrace.cli._app": {"app", "main"},
    "qmstrace.cli._ledger": {
        "copy_schema",
        "ledger",
        "ledger_check",
        "ledger_impact",
        "ledger_table",
        "ledger_thread",
    },
    "qmstrace.cli._local": {
        "check",
        "graph",
        "impact",
        "init",
        "results",
        "rules",
        "status",
        "thread",
    },
    "qmstrace.cli._options": {"Directory"},
    "qmstrace.cli._outcome": {
        "EXIT_CODES",
        "EXIT_COULD_NOT_JUDGE",
        "EXIT_FAILED",
        "EXIT_INTERNAL",
        "EXIT_OK",
        "outcome",
    },
}


def _check_cli_dependencies(path: Path) -> None:
    assert _imports(path) <= CLI_IMPORTS[path.stem]


def test_cli_owners_are_one_way_and_callers_use_the_facade() -> None:
    package = SRC / "cli"
    assert {p.stem for p in package.glob("*.py") if p.stem != "__init__"} == set(CLI_IMPORTS)
    for path in package.glob("*.py"):
        if path.stem != "__init__":
            _check_cli_dependencies(path)
    for path in SRC.rglob("*.py"):
        if path.parent != package:
            assert not any(n.startswith("qmstrace.cli.") for n in _imports(path))


@pytest.mark.parametrize(
    ("owner", "source"),
    [
        ("_local", "from qmstrace.cli import app"),
        ("_ledger", "from qmstrace.cli._app import app"),
        ("_local", "from qmstrace.cli._ledger import ledger"),
        ("_options", "from qmstrace.workspace import Workspace"),
        ("_outcome", "from qmstrace.cli._options import Directory"),
        ("_app", "from qmstrace.workspace import Workspace"),
        ("_local", "from qmstrace.infra.git import GitCli"),
        (
            "_ledger",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
            "    from qmstrace.cli._local import status",
        ),
    ],
)
def test_cli_dependency_gate_rejects_back_edges(tmp_path: Path, owner: str, source: str) -> None:
    path = tmp_path / f"{owner}.py"
    path.write_text(source + "\n")
    with pytest.raises(AssertionError):
        _check_cli_dependencies(path)


def test_only_the_csharp_syntax_module_imports_the_parser() -> None:
    """ADR-0004: tree-sitter is a runtime dependency of one module, so it can be replaced there."""
    users = sorted(
        p.relative_to(SRC).as_posix()
        for p in SRC.rglob("*.py")
        if any(n.split(".")[0] in ("tree_sitter", "tree_sitter_c_sharp") for n in _imports(p))
    )
    assert users == ["extract/csharp/_syntax.py"]


def test_only_the_report_reader_parses_xml() -> None:
    """DSN-QMT-09: a report is parsed once, safely, where its format is decided."""
    users = sorted(
        p.relative_to(SRC).as_posix()
        for p in SRC.rglob("*.py")
        if any(n.split(".")[0] == "defusedxml" for n in _imports(p))
    )
    assert users == ["extract/reports.py"]
