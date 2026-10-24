"""Local workspace-map discovery and canonical filesystem locations; never used by GitTree.

Implements: DSN-QMT-10
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from types import MappingProxyType

from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.locations import Locations, WorkspaceMap

LOCAL_MAP = Path(".qmstrace/workspace.toml")


def relative(root: Path, path: Path) -> str:
    """A legacy bare relative label; mapped sources use repo-qualified evidence instead."""
    try:
        return Path(os.path.relpath(path, root)).as_posix()
    except ValueError:
        raise CouldNotJudge(
            "A legacy relative location spans different drives and has no filesystem relpath.",
            "Fix: select a workspace map so source evidence uses repository identities "
            "instead of cross-drive filesystem paths.",
        ) from None


def _read(file: Path) -> tuple[Path, WorkspaceMap]:
    try:
        canonical = file.resolve(strict=True)
        text = canonical.read_text(encoding="utf-8-sig")
        return canonical, WorkspaceMap.parse(text, file.name)
    except (OSError, UnicodeError, RuntimeError) as exc:
        raise CouldNotJudge(
            f"Workspace map {file.name} cannot be read ({type(exc).__name__}).",
            "Fix: supply a readable UTF-8 TOML workspace map.",
        ) from None


def _roots(file: Path, spec: WorkspaceMap) -> dict[str, Path]:
    try:
        return {name: (file.parent / path).resolve() for name, path in spec.repos.items()}
    except (OSError, RuntimeError, ValueError):
        raise CouldNotJudge(
            f"Workspace map {file.name} contains an unusable path.",
            "Fix: correct its native absolute or map-relative checkout paths.",
        ) from None


def discover(
    start: Path, root: Path, config: TraceConfig, workspace: Path | None = None
) -> Locations | None:
    """Select one source, then validate its binding. Lower-priority sources stay unread."""
    selected: tuple[Path, WorkspaceMap] | None = None
    source = "explicit"
    if workspace is not None:
        selected = _read(start / workspace)
    elif selector := os.environ.get("QMSTRACE_WORKSPACE"):
        source = "environment"
        selected = _read(start / selector)
    else:
        source = "ancestor"
        for folder in (root, *root.parents):
            candidate = folder / LOCAL_MAP
            try:
                candidate.lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise CouldNotJudge(
                    "The nearest ancestor workspace map cannot be inspected.",
                    "Fix: restore access to .qmstrace/workspace.toml or select a file explicitly.",
                ) from None
            selected = _read(candidate)
            break
        if selected is None and config.version == 2:
            source = "profile"
            candidate = Path.home() / ".qmstrace/workspaces" / f"{config.workspace_profile}.toml"
            try:
                candidate.lstat()
            except FileNotFoundError:
                pass
            except OSError:
                raise CouldNotJudge(
                    "The named workspace profile cannot be inspected.",
                    "Fix: restore profile access or select a workspace file explicitly.",
                ) from None
            else:
                selected = _read(candidate)
        if selected is None and config.version == 1:
            source = "user"
            matches: list[tuple[Path, WorkspaceMap]] = []
            problems: list[str] = []
            directory = Path.home() / ".qmstrace/workspaces"
            try:
                directory.stat()
                candidates = sorted(p for p in directory.iterdir() if p.name.endswith(".toml"))
            except FileNotFoundError:
                candidates = []
            except OSError:
                raise CouldNotJudge(
                    "The user workspace-map directory cannot be read.",
                    "Fix: restore directory permissions or select a workspace file explicitly.",
                ) from None
            for candidate in candidates:
                try:
                    file, spec = _read(candidate)
                    roots = _roots(file, spec)
                    spec.validate_roots(roots, file.name)
                except CouldNotJudge as stopped:
                    problems.append(stopped.what)
                    continue
                if spec.project == config.project and root.resolve() in roots.values():
                    matches.append((file, spec))
            if problems:
                raise CouldNotJudge(
                    "User workspace-map discovery failed: " + "; ".join(problems),
                    "Fix: repair or remove every malformed candidate, or select a file explicitly.",
                )
            if len(matches) > 1:
                raise CouldNotJudge(
                    "Several user workspace maps match this project and checkout: "
                    + ", ".join(file.name for file, _ in matches)
                    + ".",
                    "Fix: select the intended map with --workspace FILE.",
                )
            selected = matches[0] if matches else None
    if selected is None:
        return None
    file, spec = selected
    roots = _roots(file, spec)
    current = root.resolve()
    spec.validate(
        config.project,
        set(config.repos),
        roots,
        current,
        file.name,
        repo=config.repo,
        ledger_repo=config.ledger_repo,
    )
    ledger = roots[spec.ledger_repo]
    if (root / "qmstrace.schema.toml").is_file() and current != ledger:
        raise CouldNotJudge(
            f"Workspace map {file.name} binds this ledger to another trace root.",
            "Fix: bind ledger_repo to the current ledger solution folder.",
        )
    for name, default in config.repos.items() if config.version == 1 else ():
        if os.path.normpath(default) == "." and (
            name != spec.ledger_repo or roots.get(name) != ledger
        ):
            raise CouldNotJudge(
                f"Workspace map {file.name} changes the ledger's self membership ({name}).",
                "Fix: preserve the schema-defined ledger member and its trace root.",
            )
    schema_file = ledger / "qmstrace.schema.toml"
    if ledger.exists() and not schema_file.is_file():
        raise CouldNotJudge(
            "The mapped ledger directory has no qmstrace.schema.toml.",
            "Fix: map ledger_repo to its solution trace root, not an enclosing Git root.",
        )
    if schema_file.is_file() and current != ledger:
        try:
            ledger_project = tomllib.loads(schema_file.read_text("utf-8-sig")).get("project")
        except (OSError, UnicodeError, tomllib.TOMLDecodeError):
            raise CouldNotJudge(
                "The mapped ledger's project identity cannot be read.",
                "Fix: restore its readable trace schema or select the intended ledger.",
            ) from None
        if ledger_project != config.project:
            raise CouldNotJudge(
                f"Mapped ledger belongs to project {ledger_project!r}, not {config.project!r}.",
                "Fix: bind ledger_repo to the intended project's solution trace root.",
            )
    if config.version == 2:
        for name, path in sorted(roots.items()):
            local = path / "qmstrace.toml"
            if not path.exists():
                continue
            try:
                header = tomllib.loads(local.read_text("utf-8-sig"))
            except (OSError, UnicodeError, tomllib.TOMLDecodeError):
                raise CouldNotJudge(
                    f"Mapped member {name} has no readable trace identity.",
                    "Fix: map each member to its v2 trace root, with a readable qmstrace.toml.",
                ) from None
            if header.get("version") != 2 or header.get("repo") != name:
                raise CouldNotJudge(
                    f"Mapped member {name} declares another repository identity or version.",
                    "Fix: correct the workspace binding; never infer identity from a folder name.",
                )
            held = header.get("schema", {})
            if isinstance(held, dict) and held.get("project", config.project) != config.project:
                raise CouldNotJudge(
                    f"Mapped member {name} belongs to another project.",
                    "Fix: select checkouts belonging to the configured project.",
                )
    return Locations(
        source,
        file.name,
        ledger,
        MappingProxyType(roots),
        spec.ledger_repo,
        next((name for name, path in roots.items() if path == current), None),
    )
