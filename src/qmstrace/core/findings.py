"""The findings catalogue — each code once: what is wrong, and the next move.

Every finding that reaches an agent ends with what to do, and where the wrong move is
tempting it says so. The wording lives here and nowhere else; the code that detects a problem
calls one of these functions. `CODES` is the index a meta-test holds against the scenarios
that emit each code.

Implements: DSN-QMT-06
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from qmstrace.core.baselines import Suspect

from qmstrace.core.model import Finding, Item, Link, Stray

# A code's first letter is its kind, and says what it fails (data architecture § Kinds of finding).
KINDS: Final = {"V": "violation", "G": "gap", "S": "suspect"}

CODES: Final = {
    "V01": "an ID declared twice — in this repo, or already in a sibling",
    "V02": "an ID of this repo's kind that does not match its pattern",
    "V03": "a link to an ID that exists nowhere this run could read",
    "V04": "a link whose source or target is a kind of item the link type does not allow",
    "V05": "a required field missing, or a value outside its list",
    "V06": "a test with no level — not under a level folder",
    "V07": "an item declared in a file that is not scanned for its type",
    "V08": "a file that cannot be read or parsed",
    "V09": "an external ID its source does not declare",
    "V10": "a controlled item changed or added without a fresh change-request citation",
    "V11": "a cited change request does not exist, is malformed, or is not accepted",
    "V12": "a cited change request does not list the item under Impacts",
    "V13": "a frozen item's heading was removed",
    "V14": "a link field that holds something other than IDs",
    "V15": "a verifies marker in a form this tool does not read",
    "V16": "an ID of this repo's kind, declared nowhere, written where it declares nothing",
    "S01": "an existing local item downstream of changed or removed frozen content needs review",
}

# Codes that never stop a baseline tag's tree being read as a snapshot. Any other violation in
# a tagged tree means its items cannot be trusted; these declare nothing, so the items stand.
SNAPSHOT_SAFE: Final = frozenset({"V16"})


def suspect(value: Suspect) -> Finding:
    """One review obligation with every root and graph version retained."""
    details = []
    for reason in value.reasons:
        old, current = reason.historical_distance, reason.current_distance
        if reason.unpinned_repo is not None:
            reach = (
                f"current reach only: distance {current} — {reason.unpinned_repo} is read from "
                "its working tree, not at that baseline — not pinned"
            )
        elif old is not None and current is not None:
            reach = f"both versions: baseline distance {old}, current distance {current}"
        elif old is not None:
            reach = f"historical-only: distance {old}"
        else:
            reach = f"current-only: distance {current}"
        if reason.edited is None:
            state = "unknown whether edited — needs review"
        else:
            state = "edited — still needs review" if reason.edited else "unchanged — needs review"
        withdrawn = ", withdrawn" if reason.root_withdrawn else ""
        repo = reason.baseline.snapshot.repo
        since = f"{reason.baseline.label} in {repo}" if repo is not None else reason.baseline.label
        details.append(
            f"{reason.root} ({reason.root_state}{withdrawn}) since {since}: {reach}; {state}"
        )
    item = value.item
    withdrawn = " [withdrawn]" if item.fields.get("Status") == "withdrawn" else ""
    return Finding(
        "S01",
        item.file,
        item.line,
        f"{item.id}{withdrawn} — " + " | ".join(details) + ".",
        "Review: check this item against the upstream change and test evidence; "
        "editing or passing tests does not record review.",
        item.id,
    )


def _either(names: Iterable[str]) -> str:
    return " or ".join(_words(name) for name in names)


def _words(name: str) -> str:
    """An item type as a reader writes it: `design_element` → design element."""
    return name.replace("_", " ")


def _a(name: str) -> str:
    """With its article: an origin clause, a requirement."""
    words = _words(name)
    return f"{'an' if words[:1] in set('aeiou') else 'a'} {words}"


def declared_twice(item: Item, first: Item) -> Finding:
    return Finding(
        "V01",
        item.file,
        item.line,
        f"{item.id} is declared twice (first at {first.file}:{first.line}).",
        "Fix: an ID names exactly one item — give one of them another ID, or, for a module "
        "or a test function, another name.",
        item.id,
    )


def declared_in_sibling(token: str, sibling: str, file: str, line: int) -> Finding:
    return Finding(
        "V01",
        file,
        line,
        f"{token} is already declared in sibling repo '{sibling}'.",
        "Fix: do not declare it here — cite it by ID, exactly like a local item. A "
        "requirement has one home.",
        token,
    )


def malformed_id(token: str, item_type: str, pattern: str, file: str, line: int) -> Finding:
    return Finding(
        "V02",
        file,
        line,
        f"{token} does not match this repo's ID pattern for {_a(item_type)} ({pattern}).",
        f"Fix: write the ID as [items.{item_type}] id_pattern says in qmstrace.toml — or, if "
        "this heading is prose, do not start it with an ID.",
        token,
    )


def no_such_item(
    link: Link, *, home: str | None, siblings_read: bool, whole_project: bool = False
) -> Finding:
    if whole_project:
        where = "in any repo of the project"
    else:
        where = "in this repo or its siblings" if siblings_read else "in this repo"
    if home:
        hint = f"declare it in {home}, or correct the ID"
    elif whole_project:
        hint = "every repo of the project was read — correct the ID"
    else:
        hint = "it may belong to another repo of the project — check the ID there, or correct it"
    return Finding(
        "V03",
        link.file,
        link.line,
        f"{link.src} → {link.marker} → {link.dst}: no such item {where}.",
        f"Fix: {hint}.",
        link.src,
        link.marker,
        link.dst,
    )


def wrong_target(link: Link, target_type: str, allowed: Iterable[str]) -> Finding:
    return Finding(
        "V04",
        link.file,
        link.line,
        f"{link.src} → {link.marker} → {link.dst}: '{link.marker}' may point at "
        f"{_either(allowed)}, not at {_a(target_type)}.",
        "Fix: point it at the right kind of item, or use the marker that fits — the trace "
        "schema's [links] lists them.",
        link.src,
        link.marker,
        link.dst,
    )


def wrong_carrier(link: Link, source_type: str, allowed: Iterable[str]) -> Finding:
    return Finding(
        "V04",
        link.file,
        link.line,
        f"{link.src} carries '{link.marker}', which {_a(source_type)} may not carry — "
        f"'{link.marker}' is carried by {_either(allowed)}.",
        "Fix: move the line to the kind of item that carries it, or remove it.",
        link.src,
        link.marker,
        link.dst,
    )


def missing_field(item: Item, key: str, allowed: Iterable[str] = ()) -> Finding:
    values = tuple(allowed)
    hint = f" — one of: {', '.join(values)}" if values else ""
    return Finding(
        "V05",
        item.file,
        item.line,
        f"{item.id} has no '{key}:' line.",
        f"Fix: add '- {key}: …' under the heading{hint}.",
        item.id,
    )


def value_not_allowed(item: Item, key: str, value: str, allowed: Iterable[str]) -> Finding:
    return Finding(
        "V05",
        item.file,
        item.line,
        f"{item.id} has {key}: '{value}', which is not an allowed value.",
        f"Fix: use one of {', '.join(allowed)} — spelled exactly so.",
        item.id,
    )


def no_level(item: Item, levels: Iterable[str]) -> Finding:
    return Finding(
        "V06",
        item.file,
        item.line,
        f"{item.id} has no test level: its file is not under a level folder.",
        f"Fix: move the file under tests/<{' | '.join(levels)}>/ — a level is information, "
        "not a rule, and it is read from where the test sits.",
        item.id,
    )


def not_scanned_here(
    token: str,
    item_type: str,
    files: Iterable[str],
    file: str,
    line: int,
    *,
    declared: Item | None = None,
) -> Finding:
    move = f"Fix: {_a(item_type)} is read from {', '.join(files)}; move it there."
    if declared is not None:  # a recap of an item declared where it is read
        move = (
            f"Fix: {token} is declared at {declared.file}:{declared.line}; here, do not start a "
            "heading with its ID — name it later in the heading or in the text."
        )
    return Finding(
        "V07",
        file,
        line,
        f"{token} is declared here, but this file is not scanned for {_a(item_type)} — so the "
        "tool cannot see it.",
        move,
        token,
    )


def id_not_first(token: str, item_type: str, files: Iterable[str], file: str, line: int) -> Finding:
    return Finding(
        "V16",
        file,
        line,
        f"{token} is in this heading but not first, so it declares nothing — and nothing else "
        "declares it.",
        f"Fix: to declare it, start a heading with it — `### {token} — <title>`, a section "
        f"number before it is fine — where {_a(item_type)} is read ({', '.join(files)}); if the "
        "heading only names it, correct the ID. Never invent the item to make the ID resolve.",
        token,
    )


def id_in_table(token: str, item_type: str, files: Iterable[str], file: str, line: int) -> Finding:
    return Finding(
        "V16",
        file,
        line,
        f"{token} starts a table row, but a table declares nothing — and nothing else declares it.",
        f"Fix: to declare it, write a heading `### {token} — <title>` where {_a(item_type)} is "
        f"read ({', '.join(files)}); if the row only lists it, correct the ID. Never invent the "
        "item to make the ID resolve.",
        token,
    )


def cannot_parse(file: str, line: int, reason: str) -> Finding:
    return Finding(
        "V08",
        file,
        line,
        f"{file} cannot be parsed: {reason}.",
        "Fix: correct the file — nothing in it can be traced until it parses.",
    )


def cannot_read(file: str) -> Finding:
    return Finding(
        "V08",
        file,
        1,
        f"{file} cannot be read as UTF-8 text.",
        "Fix: save it as UTF-8 — nothing in it can be traced until then.",
    )


def undeclared_external(link: Link, source: str, declared: Iterable[str]) -> Finding:
    listing = ", ".join(declared) or "nothing"
    return Finding(
        "V09",
        link.file,
        link.line,
        f"{link.src} → {link.marker} → {link.dst}: the {source} declares no {link.dst} (it "
        f"declares {listing}).",
        "Fix: cite a real one, or tell the developer that nothing covers this — never invent one.",
        link.src,
        link.marker,
        link.dst,
    )


def not_an_id(
    item_id: str, marker: str, token: str, file: str, line: int, fix: str | None = None
) -> Finding:
    """V14. `fix` is the extractor's own next move where its marker is not a field line."""
    said = f"'{token}' is not an ID" if token else "the line names no ID"
    return Finding(
        "V14",
        file,
        line,
        f"{item_id} → {marker}: {said}, so it links nothing.",
        fix
        or f"Fix: the '{marker}' line holds IDs only, comma-separated. If nothing real fits, "
        "remove the line and tell the developer what is missing — never invent an ID.",
        item_id,
        marker,
    )


def uncited_change(item: Item, baseline: str, state: str) -> Finding:
    return Finding(
        "V10",
        item.file,
        item.line,
        f"{item.id} is {state} since {baseline}, but cites no fresh change request.",
        "Fix: restore the item, or stop and ask for an accepted change request listing it; "
        "add its ID to Change. An old citation does not authorize another edit.",
        item.id,
    )


def invalid_request(item: Item, citation: str, detail: str) -> Finding:
    return Finding(
        "V11",
        item.file,
        item.line,
        f"{item.id} cites {citation}, which {detail}.",
        "Fix: stop and ask for an accepted change request; never invent one or approve it here.",
        item.id,
    )


def missing_impact(item: Item, citation: str) -> Finding:
    return Finding(
        "V12",
        item.file,
        item.line,
        f"{citation} does not list {item.id} under Impacts.",
        "Fix: tell the project side that the impact analysis is incomplete; do not edit the "
        "ledger to make this check pass.",
        item.id,
    )


def removed_frozen(item: Item, baseline: str) -> Finding:
    return Finding(
        "V13",
        item.file,
        item.line,
        f"{item.id}, frozen by {baseline}, has lost its heading.",
        "Fix: restore the heading, then retire the item with Status: withdrawn and a fresh "
        "accepted change request. Never delete a frozen identity.",
        item.id,
    )


def unread_marker(
    file: str,
    line: int,
    marker: str,
    form: str,
    fix: str | None = None,
    item: str | None = None,
) -> Finding:
    """A marker written in a form its extractor does not read; `fix` names the form it does —
    pytest's by default. `item` is the one item the marker was meant for, when it was meant for
    one; without it, the finding concerns every item of its file."""
    return Finding(
        "V15",
        file,
        line,
        f"a '{marker}' marker {form} — this tool does not read that form, so it links nothing.",
        fix
        or (
            f'Fix: write @pytest.mark.{marker}("ID", …) with literal IDs, directly on a test '
            "function or on its test class."
        ),
        item=item,
        marker=marker,
    )


# ── gaps — their codes and texts are the project's rules; the next move is built here ───────

GAP_HEADING: Final = (
    "gaps — coverage not met yet; only the gate (qmstrace check --strict) fails on them"
)


def unmet_rule(code: str, item: Item, text: str, fix: str) -> Finding:
    """A coverage rule not met yet — `code` and `text` come from the project's trace schema."""
    return Finding(code, item.file, item.line, f"{item.id}: {text}", f"Fix: {fix}", item.id)


def fix_refused(violation: Finding) -> str:
    return (
        f"first fix {violation.code} at {violation.file}:{violation.line} — it refuses the link "
        "this rule needs. Do not add a second line."
    )


def fix_stray(stray: Stray) -> str:
    where, marker = f"{stray.file}:{stray.line}", stray.marker
    if stray.kind == "table":
        return (
            f"the '{marker}' table row at {where} is not read — a table declares nothing; "
            f"write `{marker}: …` as a line in the item's section."
        )
    if stray.kind == "doccomment":
        return (
            f"the '{marker}:' line at {where} is in neither the first type's leading `///` doc "
            "comment nor, in a file that declares no type, the comment block the file opens "
            "with, so it is not read — move it to whichever the file has."
        )
    if stray.kind == "razor":
        return (
            f"the '{marker}:' line at {where} is not in a `@* … *@` comment above the page's "
            "first markup or code block, so it is not read — move it there, among the "
            "directives; `///` is a C# comment, which Razor renders as page text."
        )
    if stray.kind == "comment":
        return (
            f"the test attribute at {where} is in a comment, so it is not read — a commented-out "
            "test links nothing; restore the attribute or remove the comment."
        )
    if stray.kind == "outside":
        return (
            f"the '{marker}:' line at {where} is outside every item's section, so it is not "
            "read — move it under the heading of the item it belongs to, above the next "
            "heading of the same or a higher level."
        )
    return (
        f"the '{marker}:' line at {where} is outside the module docstring, so it is not "
        "read — move it into the docstring."
    )


def fix_none_here(kinds: str, subject: str) -> str:
    return (
        f"this repo declares no {kinds} — declare the type in qmstrace.toml and write it here, "
        f"or {subject} is met in another repo of the project: qmstrace ledger check, run in the "
        "ledger, judges that."
    )


def fix_none_in_project(kinds: str, subject: str) -> str:
    return (
        f"no repo of the project declares {_a(kinds)} — declare the type in the qmstrace.toml of "
        f"the repo that holds them, then write the link to {subject} there."
    )


def fix_write(form: str, fact: str, on: str | None = None) -> str:
    where = f"on the {on}, write" if on else "write"
    return f"{where} {form} — only if it is true: the link states that {fact}."


def fix_write_any(options: list[tuple[str, str]], fact: str) -> str:
    """Several ways to write one link — on each kind of item, in each repo that holds it."""
    ways = "; ".join(f"on the {on}, {form}" for on, form in options)
    return f"write one of these — {ways} — only if it is true: the link states that {fact}."


def fix_elsewhere(kinds: str, subject: str) -> str:
    """What a repo's own check adds when another repo may hold the link's source."""
    return (
        f" Or another repo of the project meets {subject} with a link from its {kinds}: qmstrace "
        "ledger check, run in the ledger, judges that."
    )


def fix_cite_sibling(kinds: str, form: str, fact: str, repos: list[str]) -> str:
    """A link whose targets this repo declares none of, while a sibling it reads declares some —
    a ledger that holds the documents (ADR-0001), or another product repo."""
    who, which = " and ".join(repos), " or ".join(repos)
    return (
        f"this repo declares no {kinds} for it to point at, but {who} "
        f"{'does' if len(repos) == 1 else 'do'}: write {form}, citing an item of {which} — only if "
        f"it is true: the link states that {fact}. If none is, declare the right one where the "
        "project keeps them, then write the link."
    )


def fix_no_target(kinds: str, form: str, *, whole_project: bool = False) -> str:
    if whole_project:
        return (
            f"no repo of the project declares {_a(kinds)} for it to point at — declare the type "
            f"where the design is kept, then add {form}."
        )
    return (
        f"this repo declares no {kinds} for it to point at — write the design here and add "
        f"{form}, or cite another repo's only if this item really serves it."
    )
