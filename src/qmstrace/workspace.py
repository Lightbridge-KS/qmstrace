"""The workspace — the one place that sequences a run: find the repo, read it, judge it.

`Workspace.open(start)` walks up to the trace configuration and reads it; `assessment()` scans
the tree, reads what lies outside the repo — the ledger's external sources, the project's
other repos — and builds the graph once. A command renders the result.

One scan function serves every tree. A sibling is read with the same function, for the item
types that carry authored IDs; its own findings are its own business and are dropped, and its
own siblings are never read.

Implements: DSN-QMT-02, DSN-QMT-07, DSN-QMT-09, DSN-QMT-11
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
from qmstrace.core.assessment import Assessment, ExternalState, Scanned, SiblingState
from qmstrace.core.baselines import BaselineState, Register, Snapshot
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
        source.state()
        tags = tuple(
            t
            for t in source.tags_reachable_from_head()
            if any(s.tag.fullmatch(t.name) for s in self.config.baselines.values())
        )
        commits = sorted({t.commit for t in tags})
        ancestry = frozenset(
            (a, b) for a in commits for b in commits if a != b and source.is_ancestor(a, b)
        )
        snapshots = {c: Snapshot(c, None) for c in commits}
        selected = judge.resolve_baselines(self.config, tags, snapshots, ancestry)
        for commit in sorted({b.snapshot.commit for b in selected}):
            tree = GitTree(source, commit)
            if CONFIG_FILE not in tree.files():
                continue
            config = _configuration(self.root, tree)
            scan = _scan(tree, config, config.item_types.values(), with_misplaced=True)
            items = tuple(i for part in scan.extracted for i in part.items)
            historical, found = TraceGraph.build(
                config,
                scan.extracted,
                Surroundings(every_sibling_read=False),
                misplaced=scan.misplaced,
            )
            problems = [f for f in found if f.code not in findings.SNAPSHOT_SAFE]
            if problems or scan.misplaced or len({i.id for i in items}) != len(items):
                tags_here = ", ".join(t.name for t in tags if t.commit == commit)
                details = "; ".join(f"{f.code} {f.file}:{f.line}: {f.what}" for f in problems)
                raise CouldNotJudge(
                    f"Historical trace data at {tags_here} ({commit}) cannot form a reliable "
                    f"snapshot: {details}",
                    "Fix: inspect the tagged configuration and source; do not replace historical "
                    "data with today's tree or rewrite the baseline tag.",
                )
            snapshots[commit] = Snapshot(commit, config, items, historical)
        baselines = judge.resolve_baselines(self.config, tags, snapshots, ancestry)
        comparisons, wrong = judge.guard(self.config, graph.items(), baselines, ancestry, register)
        return BaselineState(baselines, comparisons, register), wrong

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
