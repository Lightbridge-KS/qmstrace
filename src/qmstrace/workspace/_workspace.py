"""Public workspace and local assessment, walk and report orchestration.

Implements: DSN-QMT-02, DSN-QMT-07, DSN-QMT-09, DSN-QMT-11, DSN-QMT-14
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from qmstrace.core import judge, results, setup
from qmstrace.core.assessment import Assessment, ProjectAssessment, SiblingState
from qmstrace.core.baselines import BaselineState, Register
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.locations import Locations, LocationState, Paths
from qmstrace.core.model import Finding, Item, Link, Notice
from qmstrace.core.results import Results
from qmstrace.extract import reports
from qmstrace.extract.base import FORMS
from qmstrace.infra.files import read_optional, write_new
from qmstrace.infra.git import GitCli, IGit
from qmstrace.infra.locations import discover, relative
from qmstrace.infra.tree import ISourceTree, WorkingTree
from qmstrace.workspace._baselines import _judged_baselines
from qmstrace.workspace._discovery import (
    TreeFactory,
    _configuration,
    _find_ledger,
    _find_root,
    _ledger,
    _report_label,
)
from qmstrace.workspace._project import _unseen_in_project
from qmstrace.workspace._project import project as _project
from qmstrace.workspace._scanning import _scan
from qmstrace.workspace._setup import copy_schema as _copy_schema
from qmstrace.workspace._setup import initialize as _initialize
from qmstrace.workspace._sources import _external, _register
from qmstrace.workspace._sources import _siblings as _read_siblings

_GENERATE = "pytest --junitxml=report.xml, or dotnet test --logger trx"
_MATCHING: dict[results.ReportFormat, str] = {
    "junit": "use a report for this repo and its scanned tests, with default pytest JUnit class "
    "names (no --junit-prefix).",
    "trx": "use a TRX file from this repo's test projects. A run matches by the class and method "
    "dotnet test reports, so a test renamed or moved since the run does not match.",
}


@dataclass(frozen=True, slots=True)
class Workspace:
    """A product repo, opened: its root, its tree and its configuration."""

    root: Path
    tree: ISourceTree
    config: TraceConfig
    trees: TreeFactory
    git: IGit | None = None
    locations: Locations | None = None

    @classmethod
    def open(
        cls,
        start: Path,
        *,
        workspace: Path | None = None,
        trees: TreeFactory = WorkingTree,
        git: IGit | None = None,
        _invocation: Path | None = None,
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
        config = _configuration(root, tree)
        locations = discover(_invocation or start, root, config, workspace)
        return cls(root, tree, config, trees, git, locations)

    @classmethod
    def initialize(
        cls,
        start: Path,
        *,
        subject: str | None = None,
        key: str | None = None,
        language: str | None = None,
        workspace: Path | None = None,
    ) -> tuple[str, ...]:
        """Set up the selected directory, or refresh an existing ancestor's managed files.

        A ledger — the folder that holds `qmstrace.schema.toml` — is set up as a ledger that
        holds the project's documents (ADR-0001): its own configuration reads the schema by
        path, and its stanza names the ledger's verbs (M10c).

        A new product-repo configuration declares the item types of the repo's language, which
        its build files choose unless `language` names one (ADR-0006).
        """
        locations: Locations | None = None

        def load_config(root: Path) -> TraceConfig:
            nonlocal locations
            opened = cls.open(root, workspace=workspace, _invocation=start)
            locations = opened.locations
            return opened.config

        written = _initialize(
            start,
            load_config=load_config,
            subject=subject,
            key=key,
            language=language,
            workspace=workspace,
        )
        return ((locations.notice,) if locations else ()) + written

    @classmethod
    def copy_schema(
        cls, start: Path, names: Sequence[str] = (), *, workspace: Path | None = None
    ) -> tuple[TraceConfig, tuple[setup.Copied, ...]]:
        """In the ledger: write the project's schema into its product repos as a verified copy —
        every named repo, or every repo in [repos]; all of them, or none (D9)."""
        return (
            _copy_schema(start, names, workspace=workspace)
            if workspace
            else _copy_schema(start, names)
        )

    @classmethod
    def paths(cls, start: Path, *, workspace: Path | None = None) -> Paths:
        """Inspect configuration and locations without scanning items or reading baselines."""
        # A ledger may hold a schema without a traced configuration of its own.
        here = start.resolve()
        root = next(
            (
                p
                for p in (here, *here.parents)
                if (p / "qmstrace.toml").is_file() or (p / "qmstrace.schema.toml").is_file()
            ),
            None,
        )
        if root is None:
            _find_root(start)
            raise AssertionError("root discovery must refuse")
        if (root / "qmstrace.toml").is_file():
            config = _configuration(root, WorkingTree(root))
        else:
            config = TraceConfig.of_schema(read_optional(root / "qmstrace.schema.toml") or "")
        locations = discover(start, root, config, workspace)
        ledger = (
            locations.ledger
            if locations
            else (root if (root / "qmstrace.schema.toml").is_file() else _ledger(root, config))
        )
        states = []
        for name, default in sorted(config.repos.items()):
            path = (
                locations.roots.get(name) if locations else (ledger / default if ledger else None)
            )
            states.append(
                LocationState(
                    name,
                    relative(root, path) if path else None,
                    bool(path and (path / "qmstrace.toml").is_file()),
                    bool(path and path.resolve() == root.resolve()),
                )
            )
        return Paths(
            config.project,
            locations.notice if locations else "workspace: tracked paths (no map selected)",
            relative(root, ledger) if ledger else None,
            tuple(states),
            bool(ledger and (ledger / "qmstrace.schema.toml").is_file()),
            locations.source if locations else None,
            locations.filename if locations else None,
        )

    @staticmethod
    def save_view(path: Path, content: str) -> None:
        """Write an explicitly requested view without clobbering an existing artifact."""
        write_new(path, content)

    def assessment(self) -> Assessment:
        """Scan, read what lies around the repo, build the graph — once."""
        config = self.config
        scan = _scan(self.tree, config, config.item_types.values(), with_misplaced=True)
        ledger = self.locations.ledger if self.locations else _ledger(self.root, config)
        externals = [
            _external(ledger, config.externals[name], self.root)
            for name in sorted(config.externals)
        ]
        siblings, located, listed = self._siblings(ledger)
        declared: dict[str, list[Link]] = defaultdict(list)
        for _, _, links in siblings:
            for link in links:
                declared[link.src].append(link)
        around = Surroundings(
            siblings={s.name: items for s, items, _ in siblings if items is not None},
            every_sibling_read=located and all(items is not None for _, items, _ in siblings),
            externals={state.name: declared for state, declared in externals},
            declared={src: tuple(links) for src, links in declared.items()},
        )
        graph, violations = TraceGraph.build(
            config, scan.extracted, around, misplaced=scan.misplaced
        )
        violations += list(judge.ownership_findings(config, graph.items()))
        ways = {
            t.name: (judge.Way(FORMS[t.extractor]),)
            for t in config.item_types.values()
            if t.declared_here and t.extractor is not None
        }
        strays = [stray for part in scan.extracted for stray in part.strays]
        gaps = judge.coverage(config, graph, violations, strays, ways)
        register = _register(self.root, ledger, config)
        baseline_state, guard_findings = self._baselines(graph, register)
        violations += [*register.findings, *guard_findings]
        violations.sort(key=lambda f: (f.file, f.line, f.code, f.what))

        notices: list[Notice] = [Notice(self.locations.notice)] if self.locations else []
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
            siblings=tuple(state for state, _, _ in siblings),
            siblings_located=located,
            notices=tuple(notices),
            baseline_state=baseline_state,
            suspects=judge.suspects(graph, baseline_state.comparisons),
        )

    @classmethod
    def project(
        cls,
        start: Path,
        *,
        workspace: Path | None = None,
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
        if workspace is not None:
            return _project(start, workspace=workspace, trees=trees, gits=gits)
        return _project(start, trees=trees, gits=gits)

    @classmethod
    def project_results(
        cls, start: Path, reports: Sequence[tuple[str, Path]], *, workspace: Path | None = None
    ) -> tuple[ProjectAssessment, results.Results]:
        """In the ledger: read every repo, then the reports given — each naming the repo it
        reports — as one, matched against each repo's own automated tests (ADR-0005).

        A report inside the repo it names is labelled by its path from that repo's root; one
        outside, by its file name alone. A repo the schema does not list, a report that cannot
        be read, or reports that match no automated test refuse the whole run.
        """
        project = _project(start, workspace=workspace) if workspace else _project(start)
        ledger = _find_ledger(start)
        roots = (
            {repo.name: project.locations.roots[repo.name] for repo in project.repos}
            if project.locations
            else {repo.name: ledger / repo.location for repo in project.repos}
        )
        unknown = sorted({name for name, _ in reports if name not in roots})
        if unknown:
            raise CouldNotJudge(
                f"--report names {', '.join(unknown)}, which the schema's [repos] does not list "
                f"(it lists: {', '.join(sorted(roots)) or 'none'}).",
                "Fix: name the repo each report reports, as [repos] names it: --report REPO=FILE.",
            )
        read = _read_reports((name, roots[name], path) for name, path in reports)
        graph = project.graph
        tested = [item for item in graph.items() if item.runs_as]
        identities = {item.id: item.runs_as for item in tested}
        repos = {item.id: repo for item in tested if (repo := graph.nodes[item.id].repo)}
        view = results.summarize(project, read, identities, repos)
        if not view.matched_cases:
            named = ", ".join(f"{r.source.repo}:{r.source.label}" for r in view.reports)
            ways = " ".join(_MATCHING[f] for f in view.formats or ("junit",))
            raise CouldNotJudge(
                f"{named}: no report entry matches an automated test of the repo it names.",
                f"Fix: check each --report names the repo whose tests it ran. {ways}",
            )
        return project, view

    @classmethod
    def project_thread(
        cls,
        start: Path,
        item_id: str,
        *,
        workspace: Path | None = None,
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
        project = (
            cls.project(start, workspace=workspace, trees=trees, gits=gits)
            if workspace
            else cls.project(start, trees=trees, gits=gits)
        )
        if project.graph.node(item_id) is not None:
            return project
        raise _unseen_in_project(project, item_id)

    @classmethod
    def project_impact(
        cls,
        start: Path,
        item_ids: Iterable[str],
        *,
        workspace: Path | None = None,
        trees: TreeFactory = WorkingTree,
        gits: Callable[[Path], IGit] = GitCli,
    ) -> ProjectAssessment:
        """The ledger's check once; the whole request is refused if any start is unseen."""
        starts = sorted(set(item_ids))
        if not starts:
            raise CouldNotJudge("No starting IDs supplied.", "Fix: pass at least one item ID.")
        project = (
            cls.project(start, workspace=workspace, trees=trees, gits=gits)
            if workspace
            else cls.project(start, trees=trees, gits=gits)
        )
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

    def results(self, *report_paths: Path) -> Results:
        """Match explicitly selected reports, read as one, against one assessment of the
        working tree.

        The caller resolves relative report paths from the invocation directory, before repo
        discovery. Reports can be ignored or outside the repo; they are never scanned as items.
        A report inside the repo is labelled by its path from the root; one outside, by its file
        name alone, so no path of the machine reaches the output. Any report that cannot be read
        refuses the whole run.
        """
        read = _read_reports((None, self.root, path) for path in report_paths)
        assessment = self.assessment()
        identities = {item.id: item.runs_as for item in assessment.graph.items() if item.runs_as}
        view = results.summarize(assessment, read, identities)
        if not view.matched_cases:
            unmatched = "\n".join(f"  {run.run.identity!r}: {run.reason}" for run in view.unmatched)
            named = ", ".join(r.source.label for r in view.reports)
            ways = " ".join(_MATCHING[f] for f in view.formats or ("junit",))
            raise CouldNotJudge(
                f"{named}: no report entries match the {view.scanned_cases} scanned automated "
                f"tests.\n{unmatched}",
                f"Fix: {ways} No requirement verdicts were produced.",
            )
        return view

    def _baselines(
        self,
        graph: TraceGraph,
        register: Register,
    ) -> tuple[BaselineState, tuple[Finding, ...]]:
        if not self.config.baselines:
            return BaselineState(register=register), ()
        source = self.git or GitCli(self.root)
        return _judged_baselines(self.root, self.config, source, graph.items(), register)

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
    ) -> tuple[list[tuple[SiblingState, dict[str, Item] | None, tuple[Link, ...]]], bool, bool]:
        """Each sibling with its items (None when not read) and their own links; whether the
        siblings could be located at all; whether this repo is among the project's repos."""
        if self.locations:
            return _read_siblings(self.root, self.config, self.trees, ledger, self.locations)
        return _read_siblings(self.root, self.config, self.trees, ledger)


def _read_reports(
    given: Iterable[tuple[str | None, Path, Path]],
) -> dict[results.ReportSource, results.Report]:
    """Each report given as (the repo it reports, that repo's root, its path), read and
    labelled: by its path from that root when it is inside, else by its file name alone — never
    a path of the machine. A path given twice, two reports one label would show, a report that
    cannot be read or parsed: each refuses the whole run."""
    read: dict[results.ReportSource, results.Report] = {}
    paths: set[Path] = set()
    labels: set[tuple[str | None, str]] = set()
    for repo, root, path in given:
        label = _report_label(root, path)
        shown = f"{repo}:{label}" if repo else label
        if path in paths:
            raise CouldNotJudge(
                f"Report {shown} is given twice.",
                "Fix: name each report once; a run in two reports is combined anyway.",
            )
        if (repo, label) in labels:
            raise CouldNotJudge(
                f"Two reports would both be shown as {shown}.",
                "Fix: give them distinct file names, or copy them into the repo.",
            )
        paths.add(path)
        labels.add((repo, label))
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise CouldNotJudge(
                f"Cannot read report {shown} ({error.strerror}).",
                f"Fix: check the path, or generate a report: {_GENERATE}.",
            ) from None
        report = reports.read(payload)
        if report.problem:
            raise CouldNotJudge(
                f"{shown}: {report.problem}.",
                f"Fix: supply a pytest JUnit report or a TRX file: {_GENERATE}.",
            )
        read[results.ReportSource(label, hashlib.sha256(payload).hexdigest(), repo)] = report
    return read
