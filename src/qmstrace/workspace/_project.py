"""Project members and one assessment of their joined graph.

Implements: DSN-QMT-14
"""

from __future__ import annotations

import posixpath
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from qmstrace.core import judge
from qmstrace.core.assessment import ProjectAssessment, RepoState
from qmstrace.core.baselines import BaselineState, Comparison
from qmstrace.core.config import SchemaForm, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.model import Extracted, Finding, Item, Notice
from qmstrace.extract.base import FORMS
from qmstrace.infra.files import read_optional
from qmstrace.infra.git import GitCli, IGit
from qmstrace.infra.tree import ISourceTree, WorkingTree
from qmstrace.workspace._baselines import _baseline_notices, _judged_baselines
from qmstrace.workspace._discovery import (
    CONFIG_FILE,
    SCHEMA_FILE,
    TreeFactory,
    _configuration,
    _find_ledger,
    _same,
)
from qmstrace.workspace._scanning import _Scan, _scan
from qmstrace.workspace._sources import _external, _register


@dataclass(frozen=True, slots=True)
class _Member:
    """One repo of the project, opened for the ledger's check: its name in [repos], its root,
    where it is from the ledger, its tree and its own configuration."""

    name: str
    root: Path
    location: str
    tree: ISourceTree
    config: TraceConfig


def _members(ledger: Path, config: TraceConfig, trees: TreeFactory) -> list[_Member]:
    """Every repo the schema lists, opened — or one refusal naming every repo that cannot be
    judged with the others."""
    if not config.repos:
        raise CouldNotJudge(
            f"{SCHEMA_FILE} names no repos under [repos], so there is no project to judge.",
            'Fix: add each repo under [repos] — name = "../path", and the ledger itself as '
            '"." when it holds documents — then check again.',
        )
    problems: list[str] = []
    members: list[_Member] = []
    seen: dict[str, str] = {}
    for name, place in sorted(config.repos.items()):
        root = ledger / place
        shown = posixpath.normpath(posixpath.join(place, CONFIG_FILE))
        twin = next((other for other, path in seen.items() if _same(ledger / path, root)), None)
        if twin is not None:
            problems.append(f"{name} and {twin} name the same folder, {place}")
            continue
        seen[name] = place
        if not (root / CONFIG_FILE).is_file():
            problems.append(f"{name}: there is no {shown}")
            continue
        try:
            tree = trees(root)
            own = _configuration(root, tree)
        except CouldNotJudge as stopped:
            problems.append(f"{name}: its configuration could not be read — {stopped.what}")
            continue
        if own.schema_digest != config.schema_digest:
            itself = _same(root, ledger)
            if itself:
                move = f'replace its [schema] with path = "{SCHEMA_FILE}"'
            elif own.schema_form is SchemaForm.VERIFIED_COPY:
                move = f"run qmstrace ledger copy-schema {name}"
            else:
                move = f"point its [schema] at this ledger's {SCHEMA_FILE}, or copy it there"
            problems.append(f"{name}: {shown} holds other rules than this ledger's — {move}")
            continue
        location = posixpath.normpath(place)
        members.append(_Member(name, root.resolve(), location, tree, own))
    listed = any(_same(ledger / place, ledger) for place in config.repos.values())
    if (ledger / CONFIG_FILE).is_file() and not listed:
        problems.append(
            f"this ledger holds a {CONFIG_FILE}, but [repos] does not list it — add "
            'ledger = "." under [repos], or the documents it holds are not judged'
        )
    if problems:
        raise CouldNotJudge(
            "the project cannot be judged as a whole, because not every repo can be read with "
            "the ledger's rules — " + "; ".join(problems) + ".",
            "Fix: deal with each repo named above, then run qmstrace ledger check again — a "
            "repo left unread would make a clean result a false one.",
        )
    return members


def _unseen_in_project(project: ProjectAssessment, item_id: str) -> CouldNotJudge:
    """An unseen start in the ledger's walk: every repo was read, so the ID is not there — and
    a module's or a test's ID given without its repo is shown the IDs it may mean."""
    qualified = sorted(
        known for known in project.graph.nodes if ":" in known and known.split(":", 1)[1] == item_id
    )
    register = project.register
    reserved = sorted(
        r.id for r in register.requests if r.state == register.accepted and item_id in r.impacts
    )
    reservation = (
        f" It is listed in accepted request(s) {', '.join(reserved)}: reserved, but not declared."
        if reserved
        else ""
    )
    if qualified:
        move = (
            "Fix: a module's or a test's ID carries its repo in the ledger's walk — "
            f"{', '.join(qualified)}."
        )
    else:
        near = project.graph.closest(item_id)
        hint = f"the closest: {', '.join(near)}; " if near else ""
        move = f"Fix: check the ID — {hint}`qmstrace ledger check` reads every repo."
    return CouldNotJudge(
        f"{item_id} is not an item of the project — no repo declares or cites it.{reservation}",
        move,
    )


def project(
    start: Path,
    *,
    trees: TreeFactory = WorkingTree,
    gits: Callable[[Path], IGit] = GitCli,
) -> ProjectAssessment:
    """In the ledger: read every repo of the project — each from its working tree — and
    judge them as one graph (M10, ADR-0001).

    Each repo is scanned with its own configuration and built against the others' items,
    so its own violations stay its own; the builds are joined, and coverage, baselines and
    suspects are judged on the union. A module's or a test's ID carries its repo there.

    Raises
    ------
    CouldNotJudge
        When a repo the schema lists cannot be read, or holds other rules than the ledger's
        schema — a repo that was not read would make a clean result a false one. Every
        problem is named at once.
    """
    ledger = _find_ledger(start)
    config = TraceConfig.of_schema(read_optional(ledger / SCHEMA_FILE) or "")
    members = _members(ledger, config, trees)

    parts: dict[str, tuple[_Member, _Scan, tuple[Extracted, ...], tuple[Item, ...]]] = {}
    for member in members:
        own = member.config
        scan = _scan(member.tree, own, own.item_types.values(), with_misplaced=True)
        derived = frozenset(t.name for t in own.item_types.values() if t.derives_ids)
        extracted = tuple(
            p.qualified(member.name, member.location, derived) for p in scan.extracted
        )
        misplaced = tuple(
            replace(i, file=posixpath.normpath(posixpath.join(member.location, i.file)))
            for i in scan.misplaced
        )
        parts[member.name] = (member, scan, extracted, misplaced)
    authored = {
        name: {
            i.id: i
            for part in extracted
            for i in part.items
            if member.config.item_types[i.type].id_pattern is not None
        }
        for name, (member, _, extracted, _) in parts.items()
    }
    externals = [
        _external(ledger, config.externals[name], ledger) for name in sorted(config.externals)
    ]
    declared = {state.name: ids for state, ids in externals}

    graphs: dict[str, TraceGraph] = {}
    violations: list[Finding] = []
    forms: dict[str, judge.Form] = {}
    homes: dict[str, list[str]] = {}
    for name, (member, _, extracted, misplaced) in parts.items():
        around = Surroundings(
            siblings={other: items for other, items in authored.items() if other != name},
            every_sibling_read=True,
            externals=declared,
            whole_project=True,
        )
        graphs[name], found = TraceGraph.build(
            member.config, extracted, around, misplaced=misplaced
        )
        violations += found
        for t in member.config.item_types.values():
            if t.declared_here and t.extractor is not None:
                forms[t.name] = FORMS[t.extractor]
                homes.setdefault(t.name, []).append(name)
    union = TraceGraph.join(config, graphs)
    strays = [s for _, _, extracted, _ in parts.values() for p in extracted for s in p.strays]
    gaps = judge.coverage(
        config,
        union,
        violations,
        strays,
        forms,
        homes={t: tuple(sorted(names)) for t, names in homes.items()},
    )

    register = _register(ledger, ledger, config)
    covered = {t for scope in config.baselines.values() for t in scope.covers}
    states: list[RepoState] = []
    comparisons: list[Comparison] = []
    notices: list[Notice] = []
    judged_any = False
    for name, (member, scan, _, _) in parts.items():
        state = BaselineState(register=register)
        declares = {t.name for t in member.config.item_types.values() if t.declared_here}
        if member.config.baselines and declares & covered:
            judged_any = True
            state, wrong = _judged_baselines(
                member.root,
                member.config,
                gits(member.root),
                graphs[name].items(),
                register,
                repo=name,
                location=member.location,
            )
            violations += wrong
            comparisons += state.comparisons
            notices += _baseline_notices(name, state)
        states.append(RepoState(name, member.location, member.tree.label, scan.scanned, state))
    violations += register.findings
    violations.sort(key=lambda f: (f.file, f.line, f.code, f.what))
    if judged_any:
        notices.insert(
            0,
            Notice(
                "baselines: judged from each repo's reachable local tags — remote-tag "
                "completeness NOT VERIFIED; qmstrace never fetches"
            ),
        )
    cited = any(i.fields.get("Change") for i in union.items())
    if config.change_requests or cited:
        if register.available:
            notices.append(
                Notice(
                    f"change requests: {register.location} ({len(register.requests)} "
                    f"readable; {len(register.findings)} malformed) — working tree, not pinned"
                )
            )
        else:
            notices.append(
                Notice(
                    "change requests: NOT VERIFIED — "
                    f"{register.location or 'no configured register'} is unavailable"
                )
            )
    return ProjectAssessment(
        config=config,
        repos=tuple(states),
        graph=union,
        violations=tuple(violations),
        gaps=tuple(gaps),
        externals=tuple(state for state, _ in externals),
        register=register,
        notices=tuple(notices),
        suspects=judge.suspects(union, comparisons),
    )
