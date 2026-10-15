"""Public workspace and local assessment, walk and report orchestration.

Implements: DSN-QMT-02, DSN-QMT-07, DSN-QMT-09, DSN-QMT-11, DSN-QMT-14
"""

from __future__ import annotations

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
from qmstrace.core.model import Finding, Item, Link, Notice
from qmstrace.core.results import Results
from qmstrace.extract import reports
from qmstrace.extract.base import FORMS
from qmstrace.infra.files import write_new
from qmstrace.infra.git import GitCli, IGit
from qmstrace.infra.tree import ISourceTree, WorkingTree
from qmstrace.workspace._baselines import _judged_baselines
from qmstrace.workspace._discovery import TreeFactory, _configuration, _find_root, _ledger, _shown
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
        """Set up the selected directory, or refresh an existing ancestor's managed files.

        A ledger — the folder that holds `qmstrace.schema.toml` — is set up as a ledger that
        holds the project's documents (ADR-0001): its own configuration reads the schema by
        path, and its stanza names the ledger's verbs (M10c).
        """
        return _initialize(
            start, load_config=lambda root: cls.open(root).config, subject=subject, key=key
        )

    @classmethod
    def copy_schema(
        cls, start: Path, names: Sequence[str] = ()
    ) -> tuple[TraceConfig, tuple[setup.Copied, ...]]:
        """In the ledger: write the project's schema into its product repos as a verified copy —
        every named repo, or every repo in [repos]; all of them, or none (D9)."""
        return _copy_schema(start, names)

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
        return _project(start, trees=trees, gits=gits)

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
                f"Fix: check the path, or generate a report: {_GENERATE}.",
            ) from None
        report = reports.read(payload)
        if report.problem:
            raise CouldNotJudge(
                f"{label}: {report.problem}.",
                f"Fix: supply a pytest JUnit report or a TRX file: {_GENERATE}.",
            )
        assessment = self.assessment()
        identities = {item.id: item.runs_as for item in assessment.graph.items() if item.runs_as}
        view = results.summarize(assessment, report, identities, label)
        if not view.matched_cases:
            unmatched = "\n".join(f"  {run.run.identity!r}: {run.reason}" for run in view.unmatched)
            raise CouldNotJudge(
                f"{label}: no report entries match the {view.scanned_cases} scanned automated "
                f"tests.\n{unmatched}",
                f"Fix: {_MATCHING[report.format or 'junit']} "
                "No requirement verdicts were produced.",
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
        return _read_siblings(self.root, self.config, self.trees, ledger)
