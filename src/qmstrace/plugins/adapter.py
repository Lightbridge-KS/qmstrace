"""Validate public plugin values before they enter the internal trace graph.

Implements: DSN-QMT-17
"""

from __future__ import annotations

import types
from dataclasses import fields, is_dataclass
from typing import Literal, get_args, get_origin, get_type_hints

from qmstrace.core import model
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.plugin_api import v1

_CODES = {"parse": "V08", "missing-level": "V06", "invalid-id": "V14", "unread-marker": "V15"}


def request(path: str, text: str, item_type: ItemType, config: TraceConfig) -> v1.ExtractRequest:
    return v1.ExtractRequest(
        text,
        path,
        item_type.name,
        item_type.levels,
        tuple(config.links),
        tuple(m for m, link in config.links.items() if item_type.name in link.sources),
    )


def _typed(value: object, expected: object) -> bool:
    """Strictly validate nested, immutable DTO shapes, including bool versus int."""
    origin, args = get_origin(expected), get_args(expected)
    if origin is types.UnionType:
        return any(_typed(value, option) for option in args)
    if origin is Literal:
        return value in args
    if origin is tuple:
        if type(value) is not tuple:
            return False
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_typed(part, args[0]) for part in value)
        return len(value) == len(args) and all(
            _typed(v, t) for v, t in zip(value, args, strict=True)
        )
    if type(value) is not expected:
        return False
    if is_dataclass(value) and not isinstance(value, type):
        hints = get_type_hints(type(value))
        return all(_typed(getattr(value, f.name), hints[f.name]) for f in fields(value))
    return True


def adapt(value: object, source: v1.ExtractRequest) -> model.Extracted:
    if not isinstance(value, v1.Extraction) or not _typed(value, v1.Extraction):
        raise ValueError("extract must return immutable API v1 Extraction values")
    records: tuple[v1.Item | v1.Link | v1.Diagnostic | v1.Stray, ...] = (
        *value.items,
        *value.links,
        *value.diagnostics,
        *value.strays,
    )
    if any(v.file != source.path or v.line < 1 for v in records):
        raise ValueError("output locations must use the request path and positive line numbers")
    ids = {i.id for i in value.items}
    # Duplicate source declarations are evidence for host V01 validation, not a
    # provider fault. Keep every item and location; the set only validates link sources.
    for item in value.items:
        if (
            not item.id
            or item.type != source.item_type
            or not re_digest(item.digest)
            or (item.level is not None and item.level not in source.levels)
            or len(dict(item.fields)) != len(item.fields)
        ):
            raise ValueError("invalid item identity, type, digest, fields or level")
    for link in value.links:
        if (
            link.src not in ids
            or link.marker not in source.markers
            or not v1.ID_TOKEN.fullmatch(link.dst)
        ):
            raise ValueError("invalid link source, marker or target")
    for stray in value.strays:
        if (
            stray.marker not in source.permitted_markers
            or not stray.guidance
            or not stray.targets
            or any(not v1.ID_TOKEN.fullmatch(t) for t in stray.targets)
        ):
            raise ValueError("invalid stray marker, targets or guidance")
    return model.Extracted(
        items=tuple(
            model.Item(
                i.id, i.type, i.file, i.line, i.title, i.digest, dict(i.fields), i.level, i.runs_as
            )
            for i in value.items
        ),
        links=tuple(model.Link(k.src, k.dst, k.marker, k.file, k.line) for k in value.links),
        findings=tuple(
            model.Finding(
                _CODES[d.kind], d.file, d.line, d.what, d.next_move, d.item, d.marker, d.target
            )
            for d in value.diagnostics
        ),
        strays=tuple(
            model.Stray(
                s.marker, s.targets, s.file, s.line, item=s.item, guidance=s.guidance, kind=s.kind
            )
            for s in value.strays
        ),
    )


def re_digest(value: str) -> bool:
    return (
        value.startswith("sha256:")
        and len(value) == 71
        and all(c in "0123456789abcdef" for c in value[7:])
    )
