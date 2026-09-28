"""The import matrix — a layering rule that lives only in a document is already broken.

The load-bearing claims, each pinned by a test:

1. Each package imports only what `docs/structure/codebase-blueprint.md` § 6 allows — and
   every import is absolute, so the check above cannot be walked around.
2. Nothing imports `click`: the framework vendors it privately, and it is not installed.
3. A subpackage's `__init__.py` holds no code — no barrel re-exports.
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
    "extract": {"qmstrace.core", "qmstrace.extract", "defusedxml"},
    "infra": {"qmstrace.core", "qmstrace.infra"},
    "render": {"qmstrace.core", "qmstrace.render"},
    "workspace": {"qmstrace.core", "qmstrace.extract", "qmstrace.infra"},
    "cli": {"qmstrace", "qmstrace.core", "qmstrace.render", "qmstrace.workspace", "typer"},
}
FIRST_OR_THIRD_PARTY = ("qmstrace", "typer", "click", "defusedxml")


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
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


def test_a_subpackage_init_holds_no_code() -> None:
    for init in SRC.glob("*/__init__.py"):
        assert not init.read_text(encoding="utf-8").strip(), f"{init.relative_to(SRC)} is not empty"


# what reaching the file system looks like, in the source of an extractor
_FILE_SYSTEM_MODULES = {"os", "io", "pathlib", "shutil", "subprocess", "glob", "tempfile"}
_FILE_SYSTEM_CALLS = {"open", "read_text", "read_bytes", "write_text", "write_bytes", "iterdir"}


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
