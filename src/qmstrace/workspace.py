"""The workspace — the one place that sequences a run: find the repo, read it, judge it.

`Workspace.open(start)` walks up to the trace configuration and reads it; `assessment()` scans
the tree, reads what lies outside the repo — the ledger's external sources, the project's
other repos — and builds the graph once. A command renders the result.

One scan function serves every tree. A sibling is read with the same function, for the item
types that carry authored IDs; its own findings are its own business and are dropped, and its
own siblings are never read.

In the ledger, `Workspace.project` reads every repo of the project the same way and judges
them as one graph — the ledger's check (M10).

Implements: DSN-QMT-02, DSN-QMT-07, DSN-QMT-09, DSN-QMT-11, DSN-QMT-14
"""

from __future__ import annotations

import os
import posixpath
import re
import tomllib
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from importlib.resources import files
from pathlib import Path
from typing import Final

from qmstrace.core import findings, judge, results, setup
from qmstrace.core.assessment import (
    Assessment,
    ExternalState,
    ProjectAssessment,
    RepoState,
    Scanned,
    SiblingState,
)
from qmstrace.core.baselines import BaselineState, Comparison, Register, Snapshot
from qmstrace.core.config import ExternalSource, ItemType, SchemaForm, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.model import ID_TOKEN, Extracted, Finding, Item, Notice
from qmstrace.core.results import Results
from qmstrace.extract import change_requests, junit
from qmstrace.extract.base import FORMS, REGISTRY
from qmstrace.extract.pytest_tests import report_identity
from qmstrace.infra.externals import request_files
from qmstrace.infra.files import (
    Link,
    contained,
    read_optional,
    update_files,
    update_in,
    write_new,
)
from qmstrace.infra.git import GitCli, IGit
from qmstrace.infra.globbing import matches
from qmstrace.infra.tree import GitTree, ISourceTree, WorkingTree

CONFIG_FILE: Final = "qmstrace.toml"
SCHEMA_FILE: Final = "qmstrace.schema.toml"
_MARKDOWN: Final = ("*.md", "**/*.md", "*.qmd", "**/*.qmd")

TreeFactory = Callable[[Path], ISourceTree]


@dataclass(frozen=True, slots=True)
class _Scan:
    """What one scan of one tree found."""

    extracted: tuple[Extracted, ...]
    scanned: tuple[Scanned, ...]
    misplaced: tuple[Item, ...]


@dataclass(frozen=True, slots=True)
class _Member:
    """One repo of the project, opened for the ledger's check: its name in [repos], its root,
    where it is from the ledger, its tree and its own configuration."""

    name: str
    root: Path
    location: str
    tree: ISourceTree
    config: TraceConfig


@dataclass(frozen=True, slots=True)
class Workspace:
    """A product repo, opened: its root, its tree and its configuration."""

    root: Path
    tree: ISourceTree
    config: TraceConfig
    trees: TreeFactory
    git: IGit | None = None

    @classmethod
    def open(
        cls, start: Path, *, trees: TreeFactory = WorkingTree, git: IGit | None = None
    ) -> Workspace:
        """Find the product repo at or above `start`, and read its trace configuration.

        Raises
        ------
        CouldNotJudge
            When no trace configuration is found, when `start` is inside a ledger repo, or when
            the configuration cannot be trusted.
        """
        root = _find_root(start)
        tree = trees(root)
        return cls(root, tree, _configuration(root, tree), trees, git)

    @classmethod
    def initialize(
        cls, start: Path, *, subject: str | None = None, key: str | None = None
    ) -> tuple[str, ...]:
        """Set up the selected directory, or refresh an existing ancestor's managed files."""
        root = start.resolve()
        if not root.is_dir():
            raise CouldNotJudge(
                "The setup directory does not exist.", "Fix: create it first, then run init."
            )
        for parent in (root, *root.parents):
            if (parent / CONFIG_FILE).exists():
                root = parent
                break
            if (parent / SCHEMA_FILE).exists():
                raise CouldNotJudge(
                    "This is a ledger directory, not a product repo.",
                    "Fix: run init in a product repo.",
                )
        assets = files("qmstrace").joinpath("assets")
        current = read_optional(contained(root, CONFIG_FILE))
        if current is not None:
            if subject is not None or key is not None:
                raise CouldNotJudge(
                    "Subject options only apply when creating a configuration.",
                    "Fix: edit qmstrace.toml explicitly, then rerun init without options.",
                )
            config = cls.open(root).config
        else:
            subject, key = subject or "product", key or "PROD"
            if not re.fullmatch(r"[a-z][a-z0-9-]*", subject) or not re.fullmatch(
                r"[A-Z][A-Z0-9]*", key
            ):
                raise CouldNotJudge(
                    "Subject must be a lowercase name; key must be uppercase letters/digits.",
                    "Fix: use, for example, --subject service --key SVC.",
                )
            current = assets.joinpath("starter.toml").read_text(encoding="utf-8")
            current = current.replace("__SUBJECT__", subject).replace("__KEY__", key)
            config = TraceConfig.parse(current)
        guide_path = contained(root, "AGENTS.md")
        existing = read_optional(guide_path) or ""
        block = setup.stanza(assets.joinpath("stanza.md").read_text(encoding="utf-8"), config)
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
        return update_files(root, edits)

    @classmethod
    def copy_schema(
        cls, start: Path, names: Sequence[str] = ()
    ) -> tuple[TraceConfig, tuple[setup.Copied, ...]]:
        """In the ledger: write the project's schema into its product repos as a verified copy —
        every named repo, or every repo in [repos]; all of them, or none (D9)."""
        ledger = _find_ledger(start)
        schema_text = read_optional(ledger / SCHEMA_FILE) or ""
        config = TraceConfig.of_schema(schema_text)
        if not config.repos:
            raise CouldNotJudge(
                f"{SCHEMA_FILE} names no product repos under [repos], so there is nowhere to "
                "copy it.",
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

    @staticmethod
    def save_view(path: Path, content: str) -> None:
        """Write an explicitly requested view without clobbering an existing artifact."""
        write_new(path, content)

    def assessment(self) -> Assessment:
        """Scan, read what lies around the repo, build the graph — once."""
        config = self.config
        scan = _scan(self.tree, config, config.item_types.values(), with_misplaced=True)
        ledger = _ledger(self.root, config)
        externals = [
            _external(ledger, config.externals[name], self.root)
            for name in sorted(config.externals)
        ]
        siblings, located, listed = self._siblings(ledger)
        around = Surroundings(
            siblings={s.name: items for s, items in siblings if items is not None},
            every_sibling_read=located and all(items is not None for _, items in siblings),
            externals={state.name: declared for state, declared in externals},
        )
        graph, violations = TraceGraph.build(
            config, scan.extracted, around, misplaced=scan.misplaced
        )
        forms = {
            t.name: FORMS[t.extractor]
            for t in config.item_types.values()
            if t.declared_here and t.extractor is not None
        }
        strays = [stray for part in scan.extracted for stray in part.strays]
        gaps = judge.coverage(config, graph, violations, strays, forms)
        register = _register(self.root, ledger, config)
        baseline_state, guard_findings = self._baselines(graph, register)
        violations += [*register.findings, *guard_findings]
        violations.sort(key=lambda f: (f.file, f.line, f.code, f.what))

        notices: list[Notice] = []
        if located and config.repos and not listed:
            notices.append(
                Notice(
                    "this repo is not among the project's repos in the trace schema ([repos] "
                    f"lists {', '.join(sorted(config.repos))}) — the ledger's import will not "
                    "read it"
                )
            )
        if config.baselines:
            notices.append(
                Notice(
                    "baselines: judged from reachable local tags — remote-tag completeness "
                    "NOT VERIFIED; qmstrace never fetches"
                )
            )
            if not baseline_state.baselines:
                notices.append(
                    Notice("baselines: no matching reachable local tag — nothing frozen locally")
                )
            for baseline in baseline_state.baselines:
                historical = baseline.snapshot.graph
                if historical is not None and any(
                    n.item is None for n in historical.nodes.values()
                ):
                    notices.append(
                        Notice(
                            f"baseline {baseline.label}: historical external/sibling citations "
                            "NOT VERIFIED — snapshot traversal stops at this repo's edge"
                        )
                    )
                if baseline.snapshot.config is None:
                    notices.append(
                        Notice(
                            f"baseline {baseline.label}: before trace configuration "
                            "— freezes nothing"
                        )
                    )
                for tag in baseline.tags:
                    if not tag.annotated:
                        notices.append(
                            Notice(
                                f"baseline {tag.name}: lightweight tag — weaker evidence; "
                                "no tagger or tag date"
                            )
                        )
        if config.change_requests or any(i.fields.get("Change") for i in graph.items()):
            if register.available:
                notices.append(
                    Notice(
                        f"change requests: {register.location} ({len(register.requests)} readable; "
                        f"{len(register.findings)} malformed) — current working tree, not pinned"
                    )
                )
            else:
                notices.append(
                    Notice(
                        "change requests: NOT VERIFIED — "
                        f"{register.location or 'no configured register'} "
                        "is unavailable; fresh citations are verified at the ledger's import"
                    )
                )
        return Assessment(
            config=config,
            tree_label=self.tree.label,
            schema_location=config.schema_path,
            scanned=scan.scanned,
            graph=graph,
            violations=tuple(violations),
            gaps=tuple(gaps),
            externals=tuple(state for state, _ in externals),
            siblings=tuple(state for state, _ in siblings),
            siblings_located=located,
            notices=tuple(notices),
            baseline_state=baseline_state,
            suspects=judge.suspects(graph, baseline_state.comparisons),
        )

    def _baselines(
        self,
        graph: TraceGraph,
        register: Register,
    ) -> tuple[BaselineState, tuple[Finding, ...]]:
        if not self.config.baselines:
            return BaselineState(register=register), ()
        source = self.git or GitCli(self.root)
        return _judged_baselines(self.root, self.config, source, graph.items(), register)

    @classmethod
    def project(
        cls,
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

    @classmethod
    def project_thread(
        cls,
        start: Path,
        item_id: str,
        *,
        trees: TreeFactory = WorkingTree,
        gits: Callable[[Path], IGit] = GitCli,
    ) -> ProjectAssessment:
        """The ledger's check, once `item_id` is known to be an item of the project.

        Raises
        ------
        CouldNotJudge
            For an ID no repo declares or cites — and, for a module's or a test's ID written
            without its repo, the qualified IDs it may mean.
        """
        project = cls.project(start, trees=trees, gits=gits)
        if project.graph.node(item_id) is not None:
            return project
        raise _unseen_in_project(project, item_id)

    @classmethod
    def project_impact(
        cls,
        start: Path,
        item_ids: Iterable[str],
        *,
        trees: TreeFactory = WorkingTree,
        gits: Callable[[Path], IGit] = GitCli,
    ) -> ProjectAssessment:
        """The ledger's check once; the whole request is refused if any start is unseen."""
        starts = sorted(set(item_ids))
        if not starts:
            raise CouldNotJudge("No starting IDs supplied.", "Fix: pass at least one item ID.")
        project = cls.project(start, trees=trees, gits=gits)
        missing = [
            _unseen_in_project(project, item_id)
            for item_id in starts
            if project.graph.node(item_id) is None
        ]
        if missing:
            details = "\n".join(f"{problem.what} {problem.next_move}" for problem in missing)
            raise CouldNotJudge(
                details,
                "No impact list was produced. Declare each starting item before requesting "
                "its impact; a reservation does not establish its type or links.",
            )
        return project

    def thread(self, item_id: str) -> Assessment:
        """The assessment, once `item_id` is known to be something this run can see.

        Raises
        ------
        CouldNotJudge
            For an ID nothing here declares or cites. Where a sibling could not be read, it says
            so rather than claim the item does not exist.
        """
        assessment = self.assessment()
        if assessment.graph.node(item_id) is not None:
            return assessment
        raise self._unseen(assessment, item_id)

    def impact(self, item_ids: Iterable[str]) -> Assessment:
        """Assess once; refuse the whole request if any starting item is unseen."""
        starts = sorted(set(item_ids))
        if not starts:
            raise CouldNotJudge("No starting IDs supplied.", "Fix: pass at least one item ID.")
        assessment = self.assessment()
        missing = [
            self._unseen(assessment, item_id)
            for item_id in starts
            if assessment.graph.node(item_id) is None
        ]
        if missing:
            details = "\n".join(f"{problem.what} {problem.next_move}" for problem in missing)
            raise CouldNotJudge(
                details,
                "No impact list was produced. Declare each starting item before requesting "
                "its impact; a reservation does not establish its type or links.",
            )
        return assessment

    def results(self, report_path: Path) -> Results:
        """Match an explicitly selected report against one assessment of the working tree.

        The caller resolves relative report paths from the invocation directory, before repo
        discovery. Reports can be ignored or outside the repo; they are never scanned as items.
        """
        label = _shown(self.root, report_path)
        try:
            payload = report_path.read_bytes()
        except OSError as error:
            raise CouldNotJudge(
                f"Cannot read report {label} ({error.strerror}).",
                "Fix: check the path, or generate it with pytest --junitxml=report.xml.",
            ) from None
        report = junit.read(payload)
        if report.problem:
            raise CouldNotJudge(
                f"{label}: {report.problem}.",
                "Fix: supply a pytest JUnit report generated with --junitxml=report.xml.",
            )
        assessment = self.assessment()
        identities = {
            item.id: report_identity(item.id)
            for item in assessment.graph.items()
            if self.config.item_types[item.type].extractor == "pytest"
        }
        view = results.summarize(assessment, report, identities, label)
        if not view.matched_cases:
            unmatched = "\n".join(f"  {run.run.identity!r}: {run.reason}" for run in view.unmatched)
            raise CouldNotJudge(
                f"{label}: no report entries match the {view.scanned_cases} scanned pytest test "
                f"cases.\n{unmatched}",
                "Fix: use a report for this repo and its scanned tests, with default pytest "
                "JUnit class names (no --junit-prefix). No requirement verdicts were produced.",
            )
        return view

    def _unseen(self, assessment: Assessment, item_id: str) -> CouldNotJudge:
        """An unseen start, with the same source limits and next move in every walk."""
        unread = [s.name for s in assessment.siblings if s.declares is None]
        beyond = ""
        if not assessment.siblings_located:
            beyond = ", and the project's other repos could not be located"
        elif unread:
            beyond = f", and sibling {', '.join(unread)} could not be read"
        near = assessment.graph.closest(item_id)
        hint = f"the closest here: {', '.join(near)}; " if near else ""
        register = assessment.baseline_state.register
        reserved = sorted(
            r.id for r in register.requests if r.state == register.accepted and item_id in r.impacts
        )
        reservation = (
            f" It is listed in accepted request(s) {', '.join(reserved)}: "
            "reserved, but not declared here."
            if reserved
            else ""
        )
        return CouldNotJudge(
            f"{item_id} is not an item this run can see — nothing here declares or cites it"
            f"{beyond}.{reservation}",
            f"Fix: check the ID — {hint}`qmstrace status` lists this repo's requirements.",
        )

    def _siblings(
        self, ledger: Path | None
    ) -> tuple[list[tuple[SiblingState, dict[str, Item] | None]], bool, bool]:
        """Each sibling with its items (None when not read); whether the siblings could be
        located at all; whether this repo is among the project's repos."""
        if ledger is None:
            return [], not self.config.repos, False
        found: list[tuple[SiblingState, dict[str, Item] | None]] = []
        listed = False
        for name, relative in sorted(self.config.repos.items()):
            path = ledger / relative
            location = _shown(self.root, path)
            if _same(path, self.root):
                listed = True
                continue
            if not (path / CONFIG_FILE).is_file():
                found.append((SiblingState(name, location, None, "not reachable"), None))
                continue
            try:
                tree = self.trees(path)
                config = _configuration(path, tree)
            except CouldNotJudge as stopped:
                problem = f"its configuration could not be read — {stopped.what}"
                found.append((SiblingState(name, location, None, problem), None))
                continue
            authored = [t for t in config.item_types.values() if t.id_pattern is not None]
            scan = _scan(tree, config, authored, with_misplaced=False)
            # a sibling's files, as a reader of this repo would write them: ../service/docs/…
            items = {
                i.id: replace(i, file=posixpath.join(location, i.file))
                for part in scan.extracted
                for i in part.items
            }
            counts = Counter(item.type for item in items.values())
            declares = {t.name: counts[t.name] for t in authored if counts[t.name]}
            found.append((SiblingState(name, location, declares), items))
        return found, True, listed


# ── finding and reading the repo ────────────────────────────────────────────────────────────


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


def _find_root(start: Path) -> Path:
    here = Path(os.path.abspath(start))
    for folder in (here, *here.parents):
        if (folder / CONFIG_FILE).is_file():
            return folder
        if (folder / SCHEMA_FILE).is_file():
            raise CouldNotJudge(
                f"{folder} is a project's ledger repo — it holds {SCHEMA_FILE} — and this "
                "command runs in a product repo.",
                "Fix: run it in one of the project's product repos (the schema's [repos] names "
                "them), or point at one with -C <path>; the ledger's own verbs are under "
                "qmstrace ledger.",
            )
    raise CouldNotJudge(
        f"there is no {CONFIG_FILE} in {here} or any folder above it, so this is not a traced "
        "product repo.",
        "Fix: run qmstrace inside a product repo, or point at one with -C <path>.",
    )


def _find_ledger(start: Path) -> Path:
    here = Path(os.path.abspath(start))
    for folder in (here, *here.parents):
        if (folder / SCHEMA_FILE).is_file():
            return folder
        if (folder / CONFIG_FILE).is_file():
            try:
                pointer = tomllib.loads((folder / CONFIG_FILE).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, tomllib.TOMLDecodeError):
                pointer = {}
            ledger = pointer.get("ledger")
            where = f" — its ledger is at {ledger}" if isinstance(ledger, str) else ""
            raise CouldNotJudge(
                f"{folder} is a product repo{where} — and this command runs in the project's "
                "ledger repo.",
                f"Fix: run it where {SCHEMA_FILE} is, or point there with -C <path>.",
            )
    raise CouldNotJudge(
        f"there is no {SCHEMA_FILE} in {here} or any folder above it, so this is not a "
        "project's ledger repo.",
        "Fix: run qmstrace ledger inside the ledger repo, or point at it with -C <path>.",
    )


def _configuration(root: Path, tree: ISourceTree) -> TraceConfig:
    try:
        local = tree.read(CONFIG_FILE)
    except UnicodeDecodeError:
        raise CouldNotJudge(
            f"{CONFIG_FILE} in {root} is not UTF-8 text.", "Fix: save it as UTF-8."
        ) from None
    reference = TraceConfig.schema_reference(local)
    try:
        schema = (
            (tree.read(reference) if isinstance(tree, GitTree) else _read(root / reference))
            if reference
            else None
        )
    except UnicodeDecodeError:
        raise CouldNotJudge(
            f"Historical schema '{reference}' is not UTF-8 text.",
            "Fix: inspect the tagged schema; a current schema cannot replace it.",
        ) from None
    return TraceConfig.parse(local, schema)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def _register(root: Path, ledger: Path | None, config: TraceConfig) -> Register:
    spec = config.change_requests
    if spec is None:
        return Register()
    location = _shown(root, ledger / spec.source) if ledger else None
    files = request_files(ledger / spec.source, spec.prefix) if ledger else None
    if files is None:
        return Register(location, accepted=spec.accepted)
    requests = []
    wrong = []
    for name, text in files.items():
        file = posixpath.join(location or "", name)
        if text is None:
            wrong.append(findings.cannot_read(file))
            continue
        request_id = name.removesuffix(".md")
        if not ID_TOKEN.fullmatch(request_id):
            wrong.append(findings.cannot_parse(file, 1, "request filename is not an ID"))
            continue
        request, problem = change_requests.read(file, request_id, text)
        if request:
            requests.append(request)
        else:
            wrong.append(findings.cannot_parse(file, 1, problem or "invalid request metadata"))
    return Register(location, True, spec.accepted, tuple(requests), tuple(wrong))


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


def _judged_baselines(
    root: Path,
    config: TraceConfig,
    source: IGit,
    items: Iterable[Item],
    register: Register,
    *,
    repo: str | None = None,
    location: str = ".",
) -> tuple[BaselineState, tuple[Finding, ...]]:
    """One repo's baselines, read from its reachable tags, and the guard over its items. In
    the ledger's check, `repo` names it: its snapshots are read with the same qualified IDs and
    locations as today's items, so the two can be compared."""
    source.state()
    tags = tuple(
        t
        for t in source.tags_reachable_from_head()
        if any(s.tag.fullmatch(t.name) for s in config.baselines.values())
    )
    commits = sorted({t.commit for t in tags})
    ancestry = frozenset(
        (a, b) for a in commits for b in commits if a != b and source.is_ancestor(a, b)
    )
    snapshots = {c: Snapshot(c, None, repo=repo) for c in commits}
    selected = judge.resolve_baselines(config, tags, snapshots, ancestry)
    for commit in sorted({b.snapshot.commit for b in selected}):
        tree = GitTree(source, commit)
        if CONFIG_FILE not in tree.files():
            continue
        tagged = _configuration(root, tree)
        scan = _scan(tree, tagged, tagged.item_types.values(), with_misplaced=True)
        extracted, misplaced = scan.extracted, scan.misplaced
        if repo is not None:
            derived = frozenset(t.name for t in tagged.item_types.values() if t.derives_ids)
            extracted = tuple(p.qualified(repo, location, derived) for p in extracted)
            misplaced = tuple(
                replace(i, file=posixpath.normpath(posixpath.join(location, i.file)))
                for i in misplaced
            )
        found_items = tuple(i for part in extracted for i in part.items)
        historical, found = TraceGraph.build(
            tagged,
            extracted,
            Surroundings(every_sibling_read=False),
            misplaced=misplaced,
        )
        problems = [f for f in found if f.code not in findings.SNAPSHOT_SAFE]
        if problems or misplaced or len({i.id for i in found_items}) != len(found_items):
            tags_here = ", ".join(t.name for t in tags if t.commit == commit)
            details = "; ".join(f"{f.code} {f.file}:{f.line}: {f.what}" for f in problems)
            where = f" in {repo}" if repo is not None else ""
            raise CouldNotJudge(
                f"Historical trace data at {tags_here} ({commit}){where} cannot form a reliable "
                f"snapshot: {details}",
                "Fix: inspect the tagged configuration and source; do not replace historical "
                "data with today's tree or rewrite the baseline tag.",
            )
        snapshots[commit] = Snapshot(commit, tagged, found_items, historical, repo=repo)
    baselines = judge.resolve_baselines(config, tags, snapshots, ancestry)
    comparisons, wrong = judge.guard(config, items, baselines, ancestry, register)
    return BaselineState(baselines, comparisons, register), wrong


def _baseline_notices(repo: str, state: BaselineState) -> list[Notice]:
    """What one repo's baselines leave unverified, in the ledger's check."""
    if not state.baselines:
        return [Notice(f"baselines in {repo}: no matching reachable local tag — nothing frozen")]
    notices: list[Notice] = []
    for baseline in state.baselines:
        historical = baseline.snapshot.graph
        if historical is not None and any(n.item is None for n in historical.nodes.values()):
            notices.append(
                Notice(
                    f"baseline {baseline.label} in {repo}: historical citations outside it "
                    "NOT VERIFIED — each tagged version is read on its own"
                )
            )
        if baseline.snapshot.config is None:
            notices.append(
                Notice(
                    f"baseline {baseline.label} in {repo}: before trace configuration — "
                    "freezes nothing"
                )
            )
        for tag in baseline.tags:
            if not tag.annotated:
                notices.append(
                    Notice(
                        f"baseline {tag.name} in {repo}: lightweight tag — weaker evidence; "
                        "no tagger or tag date"
                    )
                )
    return notices


# ── the one scan function ───────────────────────────────────────────────────────────────────


def _scan(
    tree: ISourceTree, config: TraceConfig, types: Iterable[ItemType], *, with_misplaced: bool
) -> _Scan:
    files = tree.files()
    texts: dict[str, str | None] = {}
    unreadable: list[Finding] = []

    def text_of(path: str) -> str | None:
        if path not in texts:
            try:
                texts[path] = tree.read(path)
            except UnicodeDecodeError:
                texts[path] = None
                unreadable.append(findings.cannot_read(path))
        return texts[path]

    extracted: list[Extracted] = []
    scanned: list[Scanned] = []
    read_for: dict[str, set[str]] = {}
    for item_type in sorted(types, key=lambda t: t.name):
        if not item_type.declared_here or item_type.extractor is None:
            continue
        selected = [p for p in files if matches(p, item_type.files)]
        ignored = {p for p in selected if matches(p, item_type.ignore)}
        chosen = [p for p in selected if p not in ignored]
        read_for[item_type.name] = set(selected)
        extract = REGISTRY[item_type.extractor]
        before = len(extracted)
        for path in chosen:
            text = text_of(path)
            if text is not None:
                extracted.append(extract(path, text, item_type, config))
        items = sum(len(part.items) for part in extracted[before:])
        scanned.append(
            Scanned(
                item_type.name, item_type.files, item_type.ignore, len(chosen), items, len(ignored)
            )
        )

    misplaced: list[Item] = []
    if with_misplaced:
        documents = [p for p in files if matches(p, _MARKDOWN)]
        for item_type in (t for t in config.item_types.values() if t.extractor == "markdown"):
            if item_type.name not in read_for:
                continue
            for path in (p for p in documents if p not in read_for[item_type.name]):
                text = text_of(path)
                if text is not None:
                    misplaced += REGISTRY["markdown"](path, text, item_type, config).items
    extracted.append(Extracted(findings=tuple(unreadable)))
    return _Scan(tuple(extracted), tuple(scanned), tuple(misplaced))


# ── what lies around the repo ───────────────────────────────────────────────────────────────


def _ledger(root: Path, config: TraceConfig) -> Path | None:
    """Where the agreement and the project's other repos are looked for."""
    if config.schema_form is SchemaForm.OWN:
        return root
    return root / config.ledger if config.ledger else None


def _external(
    ledger: Path | None, source: ExternalSource, root: Path
) -> tuple[ExternalState, frozenset[str] | None]:
    """An external source and the IDs it declares — `None` when it could not be read."""
    if ledger is None:
        return ExternalState(source.name, source.prefix, None, None), None
    path = ledger / source.source
    text = _read(path)
    declared = source.declared_in(text) if text is not None else None
    count = len(declared) if declared is not None else None
    return ExternalState(source.name, source.prefix, _shown(root, path), count), declared


def _shown(root: Path, path: Path) -> str:
    """A path as a reader of this repo would write it — relative, and never resolved, so a
    temporary folder's real location never leaks into the output."""
    return posixpath.normpath(Path(os.path.relpath(path, root)).as_posix())


def _same(one: Path, other: Path) -> bool:
    """Whether two paths name one folder — by their text first, since in a pipeline the ledger
    they are written through may not exist; then on disk, which also sees through links."""
    if os.path.normpath(os.path.abspath(one)) == os.path.normpath(os.path.abspath(other)):
        return True
    try:
        return os.path.samefile(one, other)
    except OSError:
        return False
