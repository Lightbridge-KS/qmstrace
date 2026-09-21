"""The trace graph of one product repo — built so that an illegal link never enters it.

`TraceGraph.build` takes what the extractors found and what lies outside the repo, decides
every link, and returns the graph together with the findings about everything it refused. A
link is resolved in this order: an item of this repo, an item of a sibling, an ID of an
external source, and — when a sibling could not be read — an ID this run cannot verify.

That last home is deliberate. In a pipeline only one repo is checked out, so a citation of a
sibling's item cannot be looked up there; it passes as *not verified here* and is judged at the
ledger's import. An ID that matches this repo's own pattern is never given that benefit: this
repo was read, so it is known not to exist.

A walk over the graph is a `Closure`: `forward` follows what hangs off some items, `backward`
what they derive from. `thread` and `impact` render it, and so will the suspects — one
traversal, several renderers.
"""

from __future__ import annotations

import difflib
import re
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted, Finding, Item, Lead, Link


class Home(Enum):
    """Where a node of the graph is declared."""

    LOCAL = "this repo"
    SIBLING = "a sibling repo, read from its working tree, not pinned"
    EXTERNAL = "outside any product repo"
    UNVERIFIED = "not verified here — judged at the ledger's import"


@dataclass(frozen=True, slots=True)
class Node:
    """One end of a link. `item` is set for this repo's own items only; `repo` names a sibling
    or an external source. `title` and `where` are for display — `where` is a path as a reader
    of this repo would write it."""

    id: str
    home: Home
    type: str | None
    item: Item | None = None
    repo: str | None = None
    title: str | None = None
    where: str | None = None


class Direction(Enum):
    """Which way a walk goes. The glossary's words: a forward trace is derived, a backward one
    authored."""

    FORWARD = "forward"  # what hangs off an item: the links that point at it
    BACKWARD = "backward"  # what an item derives from: the links it declares


@dataclass(frozen=True, slots=True)
class Step:
    """One reached item: its distance, displayed parent and other links in the walk.

    The first link wins, except that ordinary backward ancestry takes precedence over an
    assumption. Otherwise an early assumption could conceal an origin reached another way.
    """

    node: Node
    distance: int
    via: Link
    also: tuple[Link, ...] = ()


@dataclass(frozen=True, slots=True)
class Closure:
    """Everything a walk reached from its starts, nearest first — each item once.

    A start is not a step unless another start, or a cycle, reaches it: an edited item below
    another changed item is still listed, which the suspect rule needs.
    """

    direction: Direction
    starts: tuple[str, ...]
    steps: Mapping[str, Step]

    def parent(self, step: Step) -> str:
        """The item on the start's side of the link that reached `step`."""
        return step.via.dst if self.direction is Direction.FORWARD else step.via.src

    def children(self, item_id: str) -> list[Step]:
        """The steps first reached from `item_id`, in the order they were reached."""
        return [step for step in self.steps.values() if self.parent(step) == item_id]


@dataclass(frozen=True, slots=True)
class Surroundings:
    """What lies outside this repo, as this run could read it.

    `siblings` maps each sibling that was read to the items it declares with authored IDs, their
    files already written as a reader of this repo would write them (`../service/…`).
    `every_sibling_read` is false when a sibling was not reachable, or when the project's other
    repos could not be located at all. `externals` maps an external source's name to the IDs it
    declares — or to `None` when the source could not be reached.
    """

    siblings: Mapping[str, Mapping[str, Item]] = field(default_factory=dict)
    every_sibling_read: bool = True
    externals: Mapping[str, frozenset[str] | None] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TraceGraph:
    """Items and the links between them. Every link in it was allowed by the trace schema."""

    nodes: Mapping[str, Node]
    links: tuple[Link, ...]
    _incoming: Mapping[str, tuple[Link, ...]]
    _outgoing: Mapping[str, tuple[Link, ...]]
    _marker_order: tuple[str, ...] = ()
    _dependencies: frozenset[str] = frozenset()  # markers that count toward no coverage

    @classmethod
    def build(
        cls,
        config: TraceConfig,
        extracted: Iterable[Extracted],
        surroundings: Surroundings | None = None,
        *,
        misplaced: Iterable[Item] = (),
    ) -> tuple[TraceGraph, list[Finding]]:
        """Build the graph, and report everything that was kept out of it.

        Parameters
        ----------
        extracted
            What the extractors found, one entry per file, in a stable order.
        surroundings
            Siblings and external sources; none means a repo on its own.
        misplaced
            Items found in files that are not scanned for their type (V07).
        """
        around = surroundings or Surroundings()
        found = list(extracted)
        foreign = {
            item_id: (repo, item.type)
            for repo, items in sorted(around.siblings.items())
            for item_id, item in items.items()
        }
        wrong: list[Finding] = [f for part in found for f in part.findings]

        local: dict[str, Item] = {}
        for item in (item for part in found for item in part.items):
            if item.id in foreign:
                wrong.append(
                    findings.declared_in_sibling(item.id, foreign[item.id][0], item.file, item.line)
                )
            elif item.id in local:
                wrong.append(findings.declared_twice(item, local[item.id]))
            else:
                local[item.id] = item
        wrong += _fields(config, local.values())
        wrong += _leads(config, (lead for part in found for lead in part.leads), foreign)
        wrong += [
            findings.not_scanned_here(
                item.id, item.type, config.item_types[item.type].files, item.file, item.line
            )
            for item in misplaced
        ]

        nodes: dict[str, Node] = {
            i: Node(i, Home.LOCAL, it.type, it, title=it.title, where=f"{it.file}:{it.line}")
            for i, it in local.items()
        }
        # Every ID the run can see is a node, cited or not — so it can be threaded. A sibling's
        # item is never this repo's own: `item` stays unset, and `items()` never lists it.
        for repo, items in sorted(around.siblings.items()):
            for item_id, item in items.items():
                where = f"{item.file}:{item.line}"
                nodes.setdefault(
                    item_id,
                    Node(
                        item_id, Home.SIBLING, item.type, repo=repo, title=item.title, where=where
                    ),
                )
        for name, declared in sorted(around.externals.items()):
            if declared is not None and name in config.externals:
                item_type = config.externals[name].item_type
                for item_id in sorted(declared):
                    nodes.setdefault(item_id, Node(item_id, Home.EXTERNAL, item_type, repo=name))
        kept: list[Link] = []
        for link in (link for part in found for link in part.links):
            if link.src not in local:
                continue  # its item was refused above, and reported there
            target, refusal = _resolve(config, around, nodes, foreign, link)
            if refusal is not None:
                wrong.append(refusal)
            elif target is not None:
                nodes.setdefault(target.id, target)
                kept.append(link)

        incoming: dict[str, list[Link]] = defaultdict(list)
        outgoing: dict[str, list[Link]] = defaultdict(list)
        for link in kept:
            incoming[link.dst].append(link)
            outgoing[link.src].append(link)
        graph = cls(
            nodes,
            tuple(kept),
            {k: tuple(v) for k, v in incoming.items()},
            {k: tuple(v) for k, v in outgoing.items()},
            tuple(config.links),
            frozenset(m for m, link in config.links.items() if not link.counts_for_coverage),
        )
        return graph, sorted(wrong, key=lambda f: (f.file, f.line, f.code, f.what))

    def node(self, item_id: str) -> Node | None:
        return self.nodes.get(item_id)

    def items(self, item_type: str | None = None) -> list[Item]:
        """This repo's own items, by ID."""
        own = (n.item for n in self.nodes.values() if n.item is not None)
        return sorted((i for i in own if item_type in (None, i.type)), key=lambda i: i.id)

    def incoming(self, item_id: str, marker: str | None = None) -> tuple[Link, ...]:
        """The links that point at an item — what hangs off it downstream."""
        return tuple(k for k in self._incoming.get(item_id, ()) if marker in (None, k.marker))

    def outgoing(self, item_id: str, marker: str | None = None) -> tuple[Link, ...]:
        """The links an item declares — what it points back at."""
        return tuple(k for k in self._outgoing.get(item_id, ()) if marker in (None, k.marker))

    def unverified(self) -> list[str]:
        """The cited IDs this run could not verify, sorted."""
        return sorted(n.id for n in self.nodes.values() if n.home is Home.UNVERIFIED)

    def forward(self, item_ids: Iterable[str]) -> Closure:
        """What hangs off the items, transitively — dependency links (`Assumes`) included."""
        return self._walk(item_ids, Direction.FORWARD)

    def backward(self, item_ids: Iterable[str]) -> Closure:
        """What the items derive from, transitively. An item reached through a dependency link
        is shown and not walked past: what an assumed item derives from is not what the
        assuming item derives from."""
        return self._walk(item_ids, Direction.BACKWARD)

    def closest(self, item_id: str, count: int = 3) -> list[str]:
        """The IDs nearest to one this graph does not know, for a next move — case ignored."""
        folded = {known.casefold(): known for known in self.nodes}
        near = difflib.get_close_matches(item_id.casefold(), sorted(folded), n=count)
        return sorted(folded[match] for match in near)

    def _walk(self, item_ids: Iterable[str], direction: Direction) -> Closure:
        starts = tuple(sorted(set(item_ids)))
        distance = dict.fromkeys(starts, 0)
        reached: dict[str, tuple[int, Link, list[Link]]] = {}
        expanded: set[str] = set()
        queue = deque(starts)
        while queue:
            current = queue.popleft()
            if current in expanded:
                continue
            arrived = reached.get(current)
            if (
                direction is Direction.BACKWARD
                and current not in starts
                and arrived is not None
                and arrived[1].marker in self._dependencies
            ):
                continue  # an assumed item ends a backward walk
            expanded.add(current)
            for link in self._neighbours(current, direction):
                other = link.src if direction is Direction.FORWARD else link.dst
                if other in reached:
                    _, first, also = reached[other]
                    if (
                        direction is Direction.BACKWARD
                        and first.marker in self._dependencies
                        and link.marker not in self._dependencies
                    ):
                        # An assumption may reach this item first, but an ordinary path
                        # still establishes ancestry. Show that path and resume the walk.
                        reached[other] = (distance[current] + 1, link, [first, *also])
                        if other not in starts:
                            distance[other] = distance[current] + 1
                        queue.append(other)
                    elif link is not first:
                        also.append(link)
                    continue
                reached[other] = (distance[current] + 1, link, [])
                distance.setdefault(other, distance[current] + 1)
                queue.append(other)
        steps = {
            item_id: Step(self.nodes[item_id], d, via, tuple(also))
            for item_id, (d, via, also) in sorted(reached.items(), key=lambda entry: entry[1][0])
        }
        return Closure(direction, starts, steps)

    def _neighbours(self, item_id: str, direction: Direction) -> list[Link]:
        """An item's links in one direction, each once, in the schema's link order then by ID."""
        links = self._incoming if direction is Direction.FORWARD else self._outgoing
        unique = {(k.src, k.dst, k.marker): k for k in links.get(item_id, ())}.values()
        order = {marker: index for index, marker in enumerate(self._marker_order)}
        forward = direction is Direction.FORWARD

        def rank(k: Link) -> tuple[int, str]:
            return order.get(k.marker, len(order)), k.src if forward else k.dst

        return sorted(unique, key=rank)


def _resolve(
    config: TraceConfig,
    around: Surroundings,
    nodes: Mapping[str, Node],
    foreign: Mapping[str, tuple[str, str]],
    link: Link,
) -> tuple[Node | None, Finding | None]:
    """The node a link points at, or the finding that keeps the link out."""
    link_type = config.links[link.marker]
    source_type = nodes[link.src].type or ""
    if source_type not in link_type.sources:
        return None, findings.wrong_carrier(link, source_type, link_type.sources)

    target: Node
    if link.dst in nodes and nodes[link.dst].home in (Home.LOCAL, Home.SIBLING):
        target = nodes[link.dst]
    elif external := next(
        (e for e in config.externals.values() if link.dst.startswith(e.prefix)), None
    ):
        declared = around.externals.get(external.name)
        if declared is not None and link.dst not in declared:
            listing = sorted(declared, key=_numbered)
            return None, findings.undeclared_external(link, external.name, listing)
        target = nodes.get(link.dst) or Node(
            link.dst, Home.EXTERNAL, external.item_type, repo=external.name
        )
    else:
        own = _own_type(config, link.dst)
        if own is not None or around.every_sibling_read:
            home = ", ".join(own.files) if own is not None else None
            return None, findings.no_such_item(
                link, home=home, siblings_read=bool(config.repos) and around.every_sibling_read
            )
        return Node(link.dst, Home.UNVERIFIED, None), None

    if target.type not in link_type.targets:
        return None, findings.wrong_target(link, target.type or "?", link_type.targets)
    return target, None


def _own_type(config: TraceConfig, item_id: str) -> ItemType | None:
    """The type this repo would declare an ID as, if it matches one of its own patterns."""
    return next(
        (
            t
            for t in config.item_types.values()
            if t.id_pattern is not None and t.declared_here and t.id_pattern.fullmatch(item_id)
        ),
        None,
    )


def _fields(config: TraceConfig, items: Iterable[Item]) -> list[Finding]:
    """V05 — required fields, and values from their lists, spelled exactly."""
    wrong: list[Finding] = []
    for item in items:
        item_type = config.item_types[item.type]
        for key in item_type.required:
            if key not in item.fields:
                wrong.append(findings.missing_field(item, key, item_type.values.get(key, ())))
        for key, allowed in item_type.values.items():
            value = item.fields.get(key)
            if value is not None and value not in allowed:
                wrong.append(findings.value_not_allowed(item, key, value, allowed))
    return wrong


def _leads(
    config: TraceConfig, leads: Iterable[Lead], foreign: Mapping[str, tuple[str, str]]
) -> list[Finding]:
    """Judge headings that start with an ID but declared nothing.

    A sibling's item declared again is V01; an ID of this type's kind that fails the pattern is
    V02. An ID matching another of this repo's types is left to V07; anything else is prose.
    """
    wrong: list[Finding] = []
    for lead in leads:
        item_type = config.item_types[lead.item_type]
        prefix = item_type.id_prefix or ""
        if lead.token in foreign:
            repo = foreign[lead.token][0]
            wrong.append(findings.declared_in_sibling(lead.token, repo, lead.file, lead.line))
        elif _own_type(config, lead.token) is not None:
            continue
        elif prefix and (lead.token.startswith(prefix) or _stem(lead.token) == _stem(prefix)):
            pattern = item_type.id_pattern.pattern if item_type.id_pattern else prefix
            wrong.append(
                findings.malformed_id(lead.token, lead.item_type, pattern, lead.file, lead.line)
            )
    return wrong


def _stem(text: str) -> str:
    return text.split("-", 1)[0]


def _numbered(item_id: str) -> tuple[int, str]:
    """Sort key: AGR-2 before AGR-10."""
    number = re.search(r"\d+$", item_id)
    return (int(number.group()) if number else 0, item_id)
