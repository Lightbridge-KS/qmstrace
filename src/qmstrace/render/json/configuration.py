"""Configuration-only projections; no scan, baseline judgment or operational path export.

Implements: DSN-QMT-12
"""

from qmstrace.core.config import TraceConfig
from qmstrace.core.locations import Locations, Paths
from qmstrace.render.json._common import location


def rules(config: TraceConfig, *, locations: Locations | None = None) -> dict[str, object]:
    return {
        "project": config.project,
        "schema": {
            "form": config.schema_form.value,
            "digest": config.schema_digest,
            "path": config.schema_path,
        },
        "version": config.version,
        "repo": config.repo,
        "workspace_profile": config.workspace_profile,
        "repos": {"ledger_repo": config.ledger_repo, "members": sorted(config.repos)},
        "repo_path_anchor": "repository identity; v1 defaults are ledger-relative",
        "subjects": [{"name": s.name, "key": s.key} for s in config.subjects.values()],
        "item_types": [
            {
                "name": t.name,
                "required": list(t.required),
                "values": {k: list(v) for k, v in t.values.items()},
                "levels": list(t.levels),
                "extractor": t.extractor,
                "id_pattern": t.id_pattern.pattern if t.id_pattern else None,
                "id_prefix": t.id_prefix,
                "files": list(t.files),
                "ignore": list(t.ignore),
                "declared_here": t.declared_here,
            }
            for t in config.item_types.values()
        ],
        "links": [
            {
                "marker": k.marker,
                "sources": list(k.sources),
                "targets": list(k.targets),
                "counts_for_coverage": k.counts_for_coverage,
            }
            for k in config.links.values()
        ],
        "rules": [
            {
                "code": r.code,
                "item_type": r.item_type,
                "direction": r.direction,
                "marker": r.marker,
                "where": dict(r.where),
                "text": r.text,
            }
            for r in config.rules
        ],
        "externals": [
            {
                "name": e.name,
                "item_type": e.item_type,
                "prefix": e.prefix,
                "source": e.source,
                "declared_as": e.declared_as.pattern,
            }
            for e in config.externals.values()
        ],
        "baselines": [
            {"name": b.name, "tag": b.tag.pattern, "covers": list(b.covers), "subject": b.subject}
            for b in config.baselines.values()
        ],
        "change_requests": {
            "prefix": config.change_requests.prefix,
            "source": config.change_requests.source,
            "accepted": config.change_requests.accepted,
        }
        if config.change_requests
        else None,
        "tables": {
            "matrix_fields": list(config.tables.matrix_fields),
            "matrix_level": config.tables.matrix_level,
        },
        "workspace": {"source": locations.source, "filename": locations.filename}
        if locations
        else None,
    }


def paths(value: Paths) -> dict[str, object]:
    return {
        "project": value.project,
        "selection": value.source,
        "workspace": {"source": value.workspace_source, "filename": value.workspace_filename}
        if value.workspace_source
        else None,
        "anchor": "repository trace roots",
        "repo": value.repo,
        "workspace_profile": value.workspace_profile,
        "ledger": {"location": location(value.ledger), "available": value.ledger_available},
        "repos": [
            {
                "name": r.name,
                "location": location(r.location),
                "available": r.available,
                "current": r.current,
            }
            for r in value.repos
        ],
    }
