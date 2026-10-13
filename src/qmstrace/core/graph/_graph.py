"""Build and join validated graphs; query and walk their links deterministically.

Implements: DSN-QMT-05, DSN-QMT-14
"""

from __future__ import annotations

import difflib
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum

from qmstrace.core import findings
from qmstrace.core.config import TraceConfig
from qmstrace.core.graph._nodes import Home, Node, Surroundings
from qmstrace.core.graph._validation import _fields, _leads, _mentions, _resolve
from qmstrace.core.model import Extracted, Finding, Item, Link


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
        misplaced = tuple(misplaced)
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
        wrong += _mentions(
            config,
            (mention for part in found for mention in part.mentions),
            set(local) | set(foreign) | {item.id for item in misplaced},
        )
        wrong += [
            findings.not_scanned_here(
                item.id,
                item.type,
                config.item_types[item.type].files,
                item.file,
                item.line,
                declared=local.get(item.id),
            )
            for item in misplaced
        ]

        nodes: dict[str, Node] = {
            i: Node(
                i,
                Home.LOCAL,
                it.type,
                it,
                title=it.title,
                where=f"{it.file}:{it.line}",
                fields=it.fields,
            )
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
                        item_id,
                        Home.SIBLING,
                        item.type,
                        repo=repo,
                        title=item.title,
                        where=where,
                        fields=item.fields,
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

        graph = cls._assemble(config, nodes, tuple(kept))
        return graph, sorted(wrong, key=lambda f: (f.file, f.line, f.code, f.what))

    @classmethod
    def join(cls, config: TraceConfig, parts: Mapping[str, TraceGraph]) -> TraceGraph:
        """The project's graph: each repo's graph, built against the others, joined.

        Every judged item stays judged and names its repo; a sibling's node gives way to the
        judged node of the same ID; every kept link is kept. An ID two repos declare was
        refused in both builds (V01), so no ID is judged twice.
        """
        nodes: dict[str, Node] = {}
        for repo, part in sorted(parts.items()):
            for node in part.nodes.values():
                if node.item is not None:
                    assert node.id not in nodes, f"{node.id} is judged in two repos"
                    nodes[node.id] = replace(node, repo=repo)
        for _, part in sorted(parts.items()):
            for node in part.nodes.values():
                nodes.setdefault(node.id, node)
        kept = tuple(link for _, part in sorted(parts.items()) for link in part.links)
        return cls._assemble(config, nodes, kept)

    def node(self, item_id: str) -> Node | None:
        return self.nodes.get(item_id)

    def items(self, item_type: str | None = None) -> list[Item]:
        """The items this run judges, by ID — one repo's own, or every repo's in the project's
        graph."""
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

    @classmethod
    def _assemble(
        cls, config: TraceConfig, nodes: Mapping[str, Node], links: tuple[Link, ...]
    ) -> TraceGraph:
        """Index already-admitted links, preserving their multiplicity and order."""
        incoming: dict[str, list[Link]] = defaultdict(list)
        outgoing: dict[str, list[Link]] = defaultdict(list)
        for link in links:
            incoming[link.dst].append(link)
            outgoing[link.src].append(link)
        return cls(
            nodes,
            links,
            {k: tuple(v) for k, v in incoming.items()},
            {k: tuple(v) for k, v in outgoing.items()},
            tuple(config.links),
            frozenset(m for m, link in config.links.items() if not link.counts_for_coverage),
        )

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
