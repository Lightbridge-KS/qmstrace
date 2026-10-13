"""Configured rules and schema-copy outcomes, rendered as plain text.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from qmstrace.core.config import CoverageRule, SchemaForm, TraceConfig
from qmstrace.core.setup import Copied

_DERIVED: Final = {"python-module": "ID: the module's path", "pytest": "ID: the test's node ID"}


def rules(config: TraceConfig) -> str:
    """What `check` holds this repo to, and whose each part is — read from the configuration."""
    own = config.schema_form is SchemaForm.OWN
    lines = [f"rules in force here — {_schema_source(config)}", ""]
    lines.append("From this repo's own schema" if own else "From the project's trace schema")
    lines += _links_block(config) + _fields_block(config) + _rules_block(config)
    lines += _outside_block(config)
    lines += ["", "From this repo's qmstrace.toml", *_declares_block(config)]
    lines += [
        "",
        "No rule has a stage: in this version every gap fails the gate (qmstrace check --strict).",
        "Rules are judged on this repo's items; whether an item is covered across the project's "
        "repos is judged in the ledger, by qmstrace ledger check.",
    ]
    return "\n".join(lines)


def _links_block(config: TraceConfig) -> list[str]:
    width = max((len(marker) for marker in config.links), default=0) + 2
    lines = [
        "",
        "  link types — a field named after a marker is the link; every link is many-to-many",
    ]
    for marker, link in config.links.items():
        line = f"    {marker:<{width}}{_words(link.sources)} → {_words(link.targets)}"
        lines.append(line + ("" if link.counts_for_coverage else " · counts toward no coverage"))
    return lines


def _fields_block(config: TraceConfig) -> list[str]:
    lines: list[str] = []
    for name, item_type in config.item_types.items():
        keys = [*item_type.required, *(k for k in item_type.values if k not in item_type.required)]
        if not keys:
            continue
        shown = [
            f"{key} ∈ {{{', '.join(item_type.values[key])}}}" if key in item_type.values else key
            for key in keys
        ]
        lines.append(f"    {name.replace('_', ' ')}: {' · '.join(shown)}")
    return ["", "  required fields", *lines] if lines else []


def _rules_block(config: TraceConfig) -> list[str]:
    if not config.rules:
        return []
    lines = ["", "  coverage rules — each unmet rule is a gap"]
    return lines + [f"    {rule.code}  {_rule(config, rule)}" for rule in config.rules]


def _outside_block(config: TraceConfig) -> list[str]:
    home = "this repo" if config.schema_form is SchemaForm.OWN else "the ledger"
    lines: list[str] = []
    for source in config.externals.values():
        lines += [
            "",
            f"  external {source.prefix}…: declared in {source.source}, in {home} — cited here, "
            "never declared here",
        ]
    if config.change_requests is not None:
        cr = config.change_requests
        lines += [
            "",
            f"  change requests {cr.prefix}…: in {cr.source}/, licensing a change when "
            f"{cr.accepted} and listing the item in Impacts; each edit needs a fresh citation",
        ]
    if config.baselines:
        lines += ["", "  baselines — reachable local tags; document changes are guarded"]
        for scope in config.baselines.values():
            subject = {"*": "every subject", None: "the subject named in the tag"}.get(
                scope.subject, scope.subject
            )
            lines.append(
                f"    {scope.name}: tags matching {scope.tag.pattern} freeze "
                f"{_words(scope.covers)} ({subject})"
            )
    return lines


def _declares_block(config: TraceConfig) -> list[str]:
    lines: list[str] = []
    if config.subjects:
        named = ", ".join(f"{s.name} (key {s.key})" for s in config.subjects.values())
        lines += ["", f"  subjects: {named}"]
    rows = []
    for item_type in (t for t in config.item_types.values() if t.declared_here):
        extractor = item_type.extractor or ""
        how = item_type.id_pattern.pattern if item_type.id_pattern else _DERIVED.get(extractor, "")
        ignored = f" · ignores {', '.join(item_type.ignore)}" if item_type.ignore else ""
        rows.append(
            [item_type.name.replace("_", " "), extractor, how, ", ".join(item_type.files) + ignored]
        )
    widths = [max((len(row[i]) for row in rows), default=0) for i in range(3)]
    lines += ["", "  declares"]
    for row in rows:
        cells = [cell.ljust(width) for cell, width in zip(row, widths, strict=False)]
        lines.append("    " + "  ".join([*cells, row[3]]))
    unscanned = [
        t.name.replace("_", " ") for t in config.item_types.values() if not t.declared_here
    ]
    if unscanned:
        lines.append(f"  knows, does not scan: {', '.join(unscanned)}")
    return lines


def _words(names: Iterable[str]) -> str:
    return ", ".join(name.replace("_", " ") for name in names)


def _schema_source(config: TraceConfig) -> str:
    local = "and this repo's qmstrace.toml"
    if config.schema_form is SchemaForm.BY_PATH:
        return f"the project's trace schema, read from {config.schema_path}, {local}"
    if config.schema_form is SchemaForm.VERIFIED_COPY:
        return f"the project's trace schema, as a verified copy under [schema], {local}"
    return "this repo's own schema, under [schema] in qmstrace.toml"


def _rule(config: TraceConfig, rule: CoverageRule) -> str:
    """One coverage rule in words, and what limits it here."""
    item = rule.item_type.replace("_", " ")
    where = "".join(f" where {k} = {v}" for k, v in rule.where.items())
    need = (
        f"an incoming {rule.marker}" if rule.direction == "incoming" else f"its own {rule.marker}"
    )
    text = f'every {item}{where} needs {need} — "{rule.text}"'
    for key, value in rule.where.items():
        others = [v for v in config.item_types[rule.item_type].values.get(key, ()) if v != value]
        if others:
            text += f" · not for {key} = {', '.join(others)}"
    sources = config.links[rule.marker].sources
    if not config.item_types[rule.item_type].declared_here:
        text += " · applies to no item here: this repo does not scan that type"
    elif rule.direction == "incoming" and not any(
        config.item_types[t].declared_here for t in sources if t in config.item_types
    ):
        text += " · cannot be met with the item types this repo scans"
    return text


def schema_copies(config: TraceConfig, copies: Iterable[Copied]) -> str:
    """What `ledger copy-schema` did: the schema it copied, then one line per repo."""
    written = list(copies)
    lines = [f"schema: {config.project} {config.schema_digest}"]
    for copy in written:
        if copy.skipped:
            lines.append(f"skipped: {copy.repo} — the ledger itself; {copy.before}")
        elif copy.changed:
            lines.append(f"updated: {copy.repo} — {copy.file}, {copy.before}")
        else:
            lines.append(f"unchanged: {copy.repo} — {copy.file}")
    copied = [copy for copy in written if not copy.skipped]
    if any(copy.changed for copy in copied):
        lines.append("Commit qmstrace.toml in each updated repo. Exit 0.")
    elif copied:
        lines.append("Every repo already carries this schema. Exit 0.")
    else:
        lines.append("Nothing was copied. Exit 0.")
    return "\n".join(lines)
