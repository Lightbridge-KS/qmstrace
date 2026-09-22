"""Independent graph versions and per-root snapshots cannot erase review obligations."""

from dataclasses import replace

import pytest

from qmstrace.core import findings
from qmstrace.core.baselines import Baseline, Comparison, Snapshot, Tag
from qmstrace.core.graph import TraceGraph
from qmstrace.core.judge import suspects
from qmstrace.core.model import Extracted, Item, Link


def name(number):
    return f"DSN-SVC-{number:02}"


def graph(config, edges, *, ids=(1, 2, 3, 4), edited=(), withdrawn=()):
    items = tuple(
        Item(
            name(i),
            "design_element",
            "docs/design/design.md",
            i,
            f"Design {i}",
            "edited" if i in edited else "same",
            {"Status": "withdrawn"} if i in withdrawn else {},
        )
        for i in ids
    )
    links = tuple(
        Link(name(dst), name(src), "Assumes", "docs/design/design.md", dst) for src, dst in edges
    )
    result, wrong = TraceGraph.build(config, [Extracted(items=items, links=links)])
    assert not wrong
    return result


def comparison(config, before, after, root=1, *, commit="abc", state="changed", aliases=()):
    baseline = Baseline(
        "designs",
        "service",
        ("design_element",),
        tuple(Tag(n, commit, False) for n in (commit, *aliases)),
        Snapshot(commit, config, tuple(before.items()), before),
    )
    old = before.node(name(root))
    current = after.node(name(root))
    return Comparison(
        name(root), baseline, old.item if old else None, current.item if current else None, state
    )


@pytest.mark.parametrize(
    "old_edges,new_edges,expected",
    [
        ([(1, 2), (2, 3)], [(1, 2), (2, 3)], {2: (1, 1), 3: (2, 2)}),
        ([(1, 2), (2, 3)], [], {2: (1, None), 3: (2, None)}),
        ([], [(1, 2), (2, 3)], {2: (None, 1), 3: (None, 2)}),
        ([(1, 2)], [(2, 3)], {2: (1, None)}),  # no mixing old root edge with new continuation
        ([(2, 3)], [(1, 2)], {2: (None, 1)}),
        ([(1, 2), (2, 3), (1, 3)], [(1, 2), (2, 3)], {2: (1, 1), 3: (1, 2)}),
        ([(1, 2), (2, 1), (2, 2)], [(1, 2), (2, 1)], {2: (1, 1)}),
    ],
)
def test_separate_walks_shortest_distances_and_cycles(service, old_edges, new_edges, expected):
    old, current = graph(service, old_edges), graph(service, new_edges, edited=(1,))
    result = suspects(current, [comparison(service, old, current)])
    assert {
        s.item.id: (s.reasons[0].historical_distance, s.reasons[0].current_distance) for s in result
    } == {name(i): distances for i, distances in expected.items()}
    assert all(not s.reasons[0].edited for s in result)


def test_new_intermediate_is_traversed_not_reported_and_missing_dependant_is_omitted(service):
    old = graph(service, [(1, 4)], ids=(1, 3, 4))
    current = graph(service, [(1, 2), (2, 3)], ids=(1, 2, 3), edited=(1, 3))
    result = suspects(current, [comparison(service, old, current)])
    assert [s.item.id for s in result] == [name(3)]
    assert result[0].distance == 2 and result[0].reasons[0].edited


def test_deleted_root_uses_historical_graph(service):
    old = graph(service, [(1, 2), (2, 3)])
    current = graph(service, [(2, 3)], ids=(2, 3))
    result = suspects(current, [comparison(service, old, current, state="removed")])
    assert [s.item.id for s in result] == [name(2), name(3)]
    assert all(s.reasons[0].current_distance is None for s in result)
    assert "(removed)" in findings.suspect(result[0]).what


@pytest.mark.parametrize("state", ["new", "frozen"])
def test_non_roots_do_not_produce_suspects(service, state):
    before = graph(service, [(1, 2)])
    assert not suspects(before, [comparison(service, before, before, state=state)])


def test_overlapping_roots_keep_each_snapshot_and_edited_state(service):
    old = graph(service, [(1, 2), (2, 3)], ids=(1, 2, 3))
    newer = graph(service, [(1, 2), (2, 3)], edited=(3,))
    current = graph(service, [(1, 2), (2, 3)], edited=(1, 2, 3))
    a = comparison(service, old, current, aliases=("alias",))
    b = comparison(service, newer, current, root=2, commit="def")
    # This downstream-only baseline cannot clear the root's chain.
    c = comparison(service, newer, current, root=3, commit="def", state="frozen")
    result = suspects(current, [c, b, a])
    assert [s.item.id for s in result] == [name(2), name(3)]
    assert [r.edited for r in result[1].reasons] == [True, False]
    assert [r.root for r in result[1].reasons] == [name(1), name(2)]
    assert "abc, alias" in findings.suspect(result[1]).what
    assert result == suspects(current, [a, b, c])


def test_withdrawn_and_edited_items_retain_reasons(service):
    old = graph(service, [(1, 2), (2, 3)])
    current = graph(service, [(1, 2), (2, 3)], edited=(1, 2), withdrawn=(1, 2))
    result = suspects(current, [comparison(service, old, current)])
    message = findings.suspect(result[0])
    assert "[withdrawn]" in message.what and "changed, withdrawn" in message.what
    assert "edited — still needs review" in message.what
    assert result[1].distance == 2
    # Reactivation is an edited dependant too, with no coverage exemption left.
    active = replace(result[0], item=replace(result[0].item, fields={}))
    assert "[withdrawn]" not in findings.suspect(active).what


def test_newness_is_relative_to_each_root_snapshot(service):
    old = graph(service, [], ids=(1, 2))
    newer = graph(service, [(2, 3)], ids=(1, 2, 3))
    current = graph(service, [(1, 3), (2, 3)], ids=(1, 2, 3), edited=(1, 2))
    a = comparison(service, old, current)
    b = comparison(service, newer, current, root=2, commit="def")
    result = suspects(current, [a, b])
    assert [s.item.id for s in result] == [name(3)]
    assert [r.root for r in result[0].reasons] == [name(2)]
