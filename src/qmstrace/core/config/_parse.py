"""Assemble a validated trace configuration from text; never read files.

Implements: DSN-QMT-03
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from qmstrace.core.config._copy import marked, schema_digest
from qmstrace.core.config._schema import (
    ONE_LINK,
    BaselineScope,
    ChangeRequests,
    CoverageRule,
    ExternalSource,
    ItemType,
    LinkType,
    SchemaForm,
    Subject,
    Tables,
)
from qmstrace.core.config._sections import (
    _baselines,
    _change_requests,
    _externals,
    _item_types,
    _links,
    _repos,
    _rules,
    _subjects,
    _tables,
)
from qmstrace.core.config._toml import _load, _Table, _version
from qmstrace.core.errors import CouldNotJudge


@dataclass(frozen=True, slots=True)
class TraceConfig:
    """Everything in force in one product repo: the project's schema and the repo's own part."""

    project: str
    ledger: str | None
    schema_form: SchemaForm
    schema_path: str | None
    schema_digest: str
    subjects: Mapping[str, Subject]
    item_types: Mapping[str, ItemType]
    links: Mapping[str, LinkType]
    rules: tuple[CoverageRule, ...]
    externals: Mapping[str, ExternalSource]
    change_requests: ChangeRequests | None
    baselines: Mapping[str, BaselineScope]
    repos: Mapping[str, str]
    tables: Tables = field(default_factory=Tables)
    version: int = 1
    repo: str | None = None
    workspace_profile: str | None = None
    ledger_repo: str | None = None

    @staticmethod
    def schema_reference(local_text: str, *, local_name: str = "qmstrace.toml") -> str | None:
        """The path a trace configuration gives for its schema, or `None` if it carries one.

        The caller reads that file and hands its text to `parse`; nothing is opened here.
        """
        schema = _load(local_text, local_name).get("schema")
        path = schema.get("path") if isinstance(schema, dict) else None
        return path if isinstance(path, str) else None

    @classmethod
    def parse(
        cls,
        local_text: str,
        schema_text: str | None = None,
        *,
        local_name: str = "qmstrace.toml",
        schema_name: str = "qmstrace.schema.toml",
    ) -> TraceConfig:
        """Validate and merge a repo's trace configuration with the project's trace schema.

        Parameters
        ----------
        local_text
            The repo's `qmstrace.toml`.
        schema_text
            The project's trace schema, when the configuration refers to it by path.

        Raises
        ------
        CouldNotJudge
            For any configuration that cannot be trusted: an unknown key, a wrong type, an
            edited copy, a rule that needs a link which counts toward no coverage. The
            message names the file and the key, and says what to do.

        Examples
        --------
        ```python
        path = TraceConfig.schema_reference(local_text)       # "../ledger/qmstrace.schema.toml"
        config = TraceConfig.parse(local_text, schema_text)
        config.item_types["requirement"].required              # ('Category', 'Origin', 'Verify-by')
        ```
        """
        local = _Table(_load(local_text, local_name), "", local_name)
        version = _version(local)
        ledger = local.opt_text("ledger") if version == 1 else None
        repo = local.text("repo") if version == 2 else None
        profile = local.text("workspace_profile") if version == 2 else None
        if profile is not None and not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", profile):
            raise CouldNotJudge(
                f"{local_name}: workspace_profile must be a portable filename stem.",
                "Fix: use lowercase letters, digits, underscores or hyphens, "
                "without a directory or .toml suffix.",
            )

        holder = local.table("schema", required=True)
        path = holder.opt_text("path")
        digest = holder.opt_text("digest")
        if path is not None:
            if digest is not None or holder.remaining():
                raise CouldNotJudge(
                    f"{local_name}: [schema] gives a path and also carries a digest or content.",
                    "Fix: a [schema] table is either a path to the project's trace schema or "
                    "a copy of it — never both.",
                )
            if schema_text is None:
                raise CouldNotJudge(
                    f"{local_name}: the project's trace schema at '{path}' could not be read.",
                    "Fix: check the project's ledger repo out where that path points, or ask "
                    "the project side for a generated copy of the schema.",
                )
            schema = _Table(_load(schema_text, schema_name), "", schema_name)
            form, stated = SchemaForm.BY_PATH, schema_digest(schema.raw)
        else:
            schema = _Table(holder.raw, "schema", local_name, skip=frozenset({"digest"}))
            stated = schema_digest(holder.raw)
            form = SchemaForm.OWN
            if digest is not None:
                form = SchemaForm.VERIFIED_COPY
                if digest != stated:
                    raise CouldNotJudge(
                        f"{local_name}: the copy of the project's trace schema under [schema] "
                        f"no longer matches its digest — it was edited by hand.",
                        "Fix: restore the generated block; to change a rule, tell the project "
                        "side and have the copy generated again.",
                    )
            holder.consume_all()

        if form is not SchemaForm.VERIFIED_COPY and marked(local_text):
            raise CouldNotJudge(
                f"{local_name}: the qmstrace markers hold a generated copy of the project's "
                "trace schema, but [schema] carries no digest — it was edited by hand.",
                "Fix: have the copy generated again — `qmstrace ledger copy-schema` in the "
                "project's ledger — or, if this repo is to hold its own schema, remove the two "
                "marker lines.",
            )
        schema_version = _version(schema)
        if schema_version != version:
            raise CouldNotJudge(
                f"{local_name}: local version {version} and schema version {schema_version} "
                "do not match.",
                "Fix: migrate the local header and regenerate the schema copy together; "
                "historical trees retain their own versions.",
            )
        repos, ledger_repo = _repos(schema, version)
        if version == 2 and repo not in {*repos, ledger_repo}:
            raise CouldNotJudge(
                f"{local_name}: repo {repo!r} is neither a member nor the ledger role.",
                "Fix: declare the intended schema member identity in the local header.",
            )
        config = cls(
            project=schema.text("project"),
            ledger=ledger,
            schema_form=form,
            schema_path=path,
            schema_digest=stated,
            subjects=_subjects(local),
            item_types=_item_types(schema, local),
            links=_links(schema),
            rules=_rules(schema),
            externals=_externals(schema),
            change_requests=_change_requests(schema),
            baselines=_baselines(schema),
            repos=repos,
            tables=_tables(schema),
            version=version,
            repo=repo,
            workspace_profile=profile,
            ledger_repo=ledger_repo,
        )
        if (
            version == 2
            and repo == ledger_repo
            and repo not in repos
            and any(t.declared_here for t in config.item_types.values())
        ):
            raise CouldNotJudge(
                f"{local_name}: the ledger role declares items but is not in repos.members.",
                "Fix: include its repository identity in the shared member set.",
            )
        schema.done()
        local.done()
        _cross_check(config, schema.file)
        return config

    @classmethod
    def of_schema(
        cls, schema_text: str, *, schema_name: str = "qmstrace.schema.toml"
    ) -> TraceConfig:
        """The project's trace schema on its own — its project, repos and rules, validated as a
        product repo would read them, with no item type declared here."""
        raw = _load(schema_text, schema_name)
        if raw.get("version") == 2:
            _, ledger = _repos(_Table(raw, "", schema_name), 2)
            placeholder = (
                f'version = 2\nrepo = {json.dumps(ledger)}\nworkspace_profile = "schema-reader"\n'
                '[schema]\npath = "qmstrace.schema.toml"\n'
            )
        else:
            placeholder = 'version = 1\n[schema]\npath = "qmstrace.schema.toml"\n'
        return cls.parse(placeholder, schema_text, local_name=schema_name, schema_name=schema_name)


def _cross_check(config: TraceConfig, schema_file: str) -> None:
    item_types = set(config.item_types)
    known = item_types | {external.item_type for external in config.externals.values()}

    def unknown_type(where: str, name: str) -> CouldNotJudge:
        return CouldNotJudge(
            f"{schema_file}: {where} names '{name}', which is not an item type "
            f"(known: {', '.join(sorted(known))}).",
            "Fix: correct the name, or declare the item type.",
        )

    for link in config.links.values():
        for name in (*link.sources, *link.targets):
            if name not in known:
                raise unknown_type(f"link '{link.marker}'", name)
    for item_type in config.item_types.values():
        if item_type.extractor not in ONE_LINK or not item_type.declared_here:
            continue
        carried = [m for m, link in config.links.items() if item_type.name in link.sources]
        if len(carried) != 1:
            said = ", ".join(carried) if carried else "none"
            raise CouldNotJudge(
                f"[items.{item_type.name}] is read by '{item_type.extractor}', whose marker — the "
                "ID that starts a test's DisplayName — names no link of its own; the schema gives "
                f"{item_type.name} {len(carried)} links to choose from ({said}).",
                f"Fix: give {item_type.name} exactly one link in the schema's [links], or read "
                "it with another extractor.",
            )

    codes: set[str] = set()
    for rule in config.rules:
        if not re.fullmatch(r"G\d{2}", rule.code) or rule.code in codes:
            raise CouldNotJudge(
                f"{schema_file}: rule code '{rule.code}' is malformed or used twice.",
                "Fix: give every coverage rule its own code, G followed by two digits.",
            )
        codes.add(rule.code)
        if rule.item_type not in item_types:
            raise unknown_type(f"rule {rule.code}", rule.item_type)
        link_type = config.links.get(rule.marker)
        if link_type is None:
            raise CouldNotJudge(
                f"{schema_file}: rule {rule.code} needs the link '{rule.marker}', which the "
                f"schema does not declare (it declares: {', '.join(config.links)}).",
                "Fix: correct the marker's name.",
            )
        if not link_type.counts_for_coverage:
            raise CouldNotJudge(
                f"{schema_file}: rule {rule.code} needs '{rule.marker}', a link that counts "
                "toward no coverage.",
                "Fix: remove the rule — such a link carries suspicion and impact only.",
            )
        end = link_type.targets if rule.direction == "incoming" else link_type.sources
        if rule.item_type not in end:
            raise CouldNotJudge(
                f"{schema_file}: rule {rule.code} asks every {rule.item_type} for an "
                f"{rule.direction} '{rule.marker}', but '{rule.marker}' goes from "
                f"{' or '.join(link_type.sources)} to {' or '.join(link_type.targets)} — no "
                f"{rule.item_type} could ever meet it.",
                "Fix: turn the rule round (incoming ↔ outgoing), or name the item type the link "
                "really reaches.",
            )
        item_type = config.item_types[rule.item_type]
        for key, value in rule.where.items():
            allowed = item_type.values.get(key)
            if key not in item_type.fields or (allowed is not None and value not in allowed):
                raise CouldNotJudge(
                    f"{schema_file}: rule {rule.code} narrows by {key} = '{value}', which "
                    f"'{rule.item_type}' does not declare.",
                    "Fix: use a field and a value the item type lists.",
                )

    for scope in config.baselines.values():
        for name in scope.covers:
            if name not in item_types:
                raise unknown_type(f"baseline '{scope.name}'", name)
    _check_tables(config, schema_file)


def _check_tables(config: TraceConfig, schema_file: str) -> None:
    """Each field `[tables.matrix]` names is one the requirement type declares, and none can be
    mistaken for a column the matrix derives on its own (ADR-0005)."""
    requirement = config.item_types.get("requirement")
    declared = requirement.fields if requirement is not None else frozenset()
    seen: set[str] = set()
    for name in config.tables.matrix_fields:
        where = f"{schema_file}: [tables.matrix] fields lists '{name}'"
        if name in seen:
            raise CouldNotJudge(f"{where} twice.", "Fix: list each field once.")
        seen.add(name)
        if name in config.links:
            raise CouldNotJudge(
                f"{where}, which is a link marker — what it points at is a column of its own.",
                f"Fix: remove '{name}' from the list.",
            )
        if name == "title" or name in config.item_types:
            raise CouldNotJudge(
                f"{where}, which is also the name of a column the matrix derives.",
                "Fix: remove it, or rename the field in the schema.",
            )
        if name not in declared:
            known = ", ".join(sorted(f for f in declared if f not in config.links)) or "none"
            raise CouldNotJudge(
                f"{where}, which the requirement type does not declare (it declares: {known}).",
                "Fix: list a field the requirement type declares under required or values.",
            )
    level = config.tables.matrix_level
    if level is None:
        return
    verifies = config.links.get("verifies")
    cases = [t for t in verifies.sources if t in verifies.targets] if verifies else []
    where = f"{schema_file}: [tables.matrix] level names '{level}'"
    if not cases:
        raise CouldNotJudge(
            f"{where}, but the schema has no test-case type — none is both a source and a "
            "target of verifies.",
            "Fix: remove level; a test's level then comes from where it sits.",
        )
    for case in cases:
        if level not in config.item_types[case].fields:
            raise CouldNotJudge(
                f"{where}, which the {case} type does not declare.",
                f"Fix: declare {level} on [item_types.{case}] under required or values, or "
                "name a field it declares.",
            )
