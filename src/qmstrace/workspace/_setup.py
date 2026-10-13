"""Setup and schema-copy orchestration; writes remain transactional.

Implements: DSN-QMT-11
"""

from __future__ import annotations

import os
import posixpath
import re
from collections.abc import Callable, Sequence
from importlib.resources import files
from pathlib import Path

from qmstrace.core import setup
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.infra.files import Link, contained, read_optional, update_files, update_in
from qmstrace.workspace._discovery import CONFIG_FILE, SCHEMA_FILE, _find_ledger, _same


def _links_for_claude(root: Path) -> bool:
    """Link the skill into Claude Code's folder only where the repo already has one: `.claude/`
    a plain folder, and its `skills/` not already the folder the skill lives in (one folder,
    linked either way round) nor a link to anywhere else."""
    claude = root / ".claude"
    if not claude.is_dir() or claude.is_symlink():
        return False
    skills = claude / "skills"
    if skills.resolve() == (root / ".agents" / "skills").resolve():
        return False
    return not skills.is_symlink()


def initialize(
    start: Path,
    *,
    load_config: Callable[[Path], TraceConfig],
    subject: str | None = None,
    key: str | None = None,
) -> tuple[str, ...]:
    """Set up the selected directory, or refresh an existing ancestor's managed files.

    A ledger — the folder that holds `qmstrace.schema.toml` — is set up as a ledger that
    holds the project's documents (ADR-0001): its own configuration reads the schema by
    path, and its stanza names the ledger's verbs (M10c).
    """
    root = start.resolve()
    if not root.is_dir():
        raise CouldNotJudge(
            "The setup directory does not exist.", "Fix: create it first, then run init."
        )
    for parent in (root, *root.parents):
        if (parent / CONFIG_FILE).exists() or (parent / SCHEMA_FILE).exists():
            root = parent
            break
    ledger = (root / SCHEMA_FILE).is_file()
    assets = files("qmstrace").joinpath("assets")
    current = read_optional(contained(root, CONFIG_FILE))
    if current is not None:
        if subject is not None or key is not None:
            raise CouldNotJudge(
                "Subject options only apply when creating a configuration.",
                "Fix: edit qmstrace.toml explicitly, then rerun init without options.",
            )
        config = load_config(root)
    else:
        subject, key = subject or "product", key or "PROD"
        if not re.fullmatch(r"[a-z][a-z0-9-]*", subject) or not re.fullmatch(
            r"[A-Z][A-Z0-9]*", key
        ):
            raise CouldNotJudge(
                "Subject must be a lowercase name; key must be uppercase letters/digits.",
                "Fix: use, for example, --subject service --key SVC.",
            )
        starter = "ledger-starter.toml" if ledger else "starter.toml"
        current = assets.joinpath(starter).read_text(encoding="utf-8")
        current = current.replace("__SUBJECT__", subject).replace("__KEY__", key)
        schema = read_optional(root / SCHEMA_FILE) if ledger else None
        config = TraceConfig.parse(current, schema)
    guide_path = contained(root, "AGENTS.md")
    existing = read_optional(guide_path) or ""
    template = assets.joinpath("stanza.md").read_text(encoding="utf-8")
    block = setup.stanza(template, config, ledger=ledger)
    if os.path.lexists(root / setup.LEGACY_SKILL):
        raise CouldNotJudge(
            "The qmstrace skill has moved to .agents/skills/qmstrace/.",
            "Fix: keep any local edits elsewhere, remove .qmstrace/, then run init again.",
        )
    skill = assets.joinpath("skill/SKILL.md").read_text(encoding="utf-8")
    prior_skill = read_optional(contained(root, setup.SKILL_FILE))
    if prior_skill is not None and prior_skill != skill:
        raise CouldNotJudge(
            "The installed qmstrace skill differs from this version.",
            f"Fix: preserve any local edits, remove {setup.SKILL_FILE}, then rerun init.",
        )
    edits: dict[str, str | Link] = {
        CONFIG_FILE: current,
        "AGENTS.md": setup.guide(existing, block),
        setup.SKILL_FILE: skill,
    }
    if _links_for_claude(root):
        edits[setup.CLAUDE_LINK] = Link(setup.CLAUDE_LINK_TARGET)
    if any(t.extractor == "pytest" for t in config.item_types.values()):
        selected = False
        for name in (
            "pytest.toml",
            ".pytest.toml",
            "pytest.ini",
            ".pytest.ini",
            "pyproject.toml",
            "tox.ini",
            "setup.cfg",
        ):
            source = read_optional(contained(root, name))
            if source is None:
                continue
            section = setup.pytest_section(name, source)
            if section is not None:
                edits[name] = setup.register_marker(name, source, section)
                selected = True
                break
        if not selected:
            source = read_optional(contained(root, "pyproject.toml"))
            name = "pyproject.toml" if source is not None else "pytest.ini"
            section = "tool.pytest.ini_options" if source is not None else "pytest"
            edits[name] = setup.register_marker(name, source or "", section)
    written = update_files(root, edits)
    if ledger and not any(_same(root / place, root) for place in config.repos.values()):
        written += (
            f'next: list this ledger in {SCHEMA_FILE} under [repos] — ledger = "." — so '
            "qmstrace ledger check reads its documents; init does not edit the schema",
        )
    return written


def copy_schema(
    start: Path, names: Sequence[str] = ()
) -> tuple[TraceConfig, tuple[setup.Copied, ...]]:
    """In the ledger: write the project's schema into its product repos as a verified copy —
    every named repo, or every repo in [repos]; all of them, or none (D9)."""
    ledger = _find_ledger(start)
    schema_text = read_optional(ledger / SCHEMA_FILE) or ""
    config = TraceConfig.of_schema(schema_text)
    if not config.repos:
        raise CouldNotJudge(
            f"{SCHEMA_FILE} names no product repos under [repos], so there is nowhere to copy it.",
            'Fix: add each product repo under [repos] — name = "../path" — then copy again.',
        )
    unknown = [name for name in names if name not in config.repos]
    if unknown:
        raise CouldNotJudge(
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not in the "
            f"schema's [repos] (it names: {', '.join(sorted(config.repos))}).",
            "Fix: name a repo the schema lists, or add it under [repos] first — a repo the "
            "project does not list cannot carry its rules.",
        )
    block = setup.schema_block(schema_text, config.project)
    source = (ledger / SCHEMA_FILE).resolve()
    problems: list[str] = []
    planned: list[tuple[Path, str, setup.Copied]] = []
    reports: list[setup.Copied] = []
    for name in dict.fromkeys(names) if names else sorted(config.repos):
        place = config.repos[name]
        root = (ledger / place).resolve()
        shown = posixpath.normpath(posixpath.join(place, CONFIG_FILE))
        if _same(ledger / place, ledger):  # the ledger reads the schema it holds, by path
            reason = setup.ledger_itself(read_optional(ledger / CONFIG_FILE))
            reports.append(setup.Copied(name, shown, False, reason, skipped=True))
            continue
        local = read_optional(root / CONFIG_FILE) if root.is_dir() else None
        if local is None:
            problems.append(f"{name}: there is no {shown}")
            continue
        try:
            held = setup.held_schema(local, shown)
            if held.kind == "own":
                problems.append(
                    f"{name}: {shown} holds a schema of its own — replace its [schema] "
                    f'with path = "…" to this ledger\'s {SCHEMA_FILE} first'
                )
                continue
            if held.kind == "path" and (root / (held.path or "")).resolve() != source:
                problems.append(
                    f"{name}: {shown} reads the schema at {held.path}, not this ledger's "
                    f"{SCHEMA_FILE}"
                )
                continue
            if held.kind == "copy" and held.project not in (None, config.project):
                problems.append(
                    f"{name}: {shown} carries project {held.project}'s schema, not "
                    f"{config.project}'s"
                )
                continue
            updated = setup.copy_schema(local, held, block, shown)
        except CouldNotJudge as stopped:
            problems.append(f"{name}: {stopped.what} {stopped.next_move}")
            continue
        before = setup.before_copy(held, config.schema_digest)
        copied = setup.Copied(name, shown, updated != local, before)
        planned.append((root, updated, copied))
        reports.append(copied)
    if problems:
        raise CouldNotJudge(
            "the schema could not be copied into every repo, so nothing was written — "
            + "; ".join(problems)
            + ".",
            "Fix: deal with each repo named above, then run qmstrace ledger copy-schema again.",
        )
    update_in({root: {CONFIG_FILE: text} for root, text, _ in planned})
    return config, tuple(reports)
