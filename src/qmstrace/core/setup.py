"""Pure edits for setup: managed guide blocks and existing pytest configuration."""

from __future__ import annotations

import configparser
import json
import re
import tomllib

from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge

BEGIN = "<!-- qmstrace:begin"
END = "<!-- qmstrace:end -->"
MARKER = "verifies(*ids): trace the items this test actually verifies"


def stanza(template: str, config: TraceConfig) -> str:
    return template.format(
        project=config.project,
        subjects=", ".join(f"{s.name} ({s.key})" for s in config.subjects.values())
        or "none declared",
        items="; ".join(
            f"{t.name} `{t.id_pattern.pattern if t.id_pattern else t.extractor}` in "
            + ", ".join(f"`{p}`" for p in t.files)
            for t in config.item_types.values()
            if t.declared_here
        ),
    )


def guide(original: str, block: str) -> str:
    if BEGIN not in original and END not in original:
        return original + ("\n" if original.endswith("\n") else "\n\n" if original else "") + block
    if original.count(BEGIN) != 1 or original.count(END) != 1:
        raise CouldNotJudge(
            "The agent guide has conflicting qmstrace markers.",
            "Fix: keep exactly one begin/end pair, then run init again.",
        )
    start, end = original.index(BEGIN), original.index(END)
    if end < start:
        raise CouldNotJudge(
            "The agent guide closes its qmstrace block before it begins.",
            "Fix: repair the begin/end pair, then run init again.",
        )
    return original[:start] + block.rstrip("\n") + original[end + len(END) :]


def pytest_section(name: str, source: str) -> str | None:
    """Return the active section in one candidate, in pytest's discovery order."""
    try:
        if name.endswith(".toml"):
            data = tomllib.loads(source)
            if name != "pyproject.toml":
                return "pytest"
            tool = data.get("tool", {}).get("pytest", {})
            if "ini_options" in tool and len(tool) > 1:
                raise ValueError("Both native pytest and ini_options settings are present")
            if "ini_options" in tool:
                return "tool.pytest.ini_options"
            return "tool.pytest" if "pytest" in data.get("tool", {}) else None
        data_ini = configparser.ConfigParser(interpolation=None)
        data_ini.read_string(source)
        section = "tool:pytest" if name == "setup.cfg" else "pytest"
        return section if name in {"pytest.ini", ".pytest.ini"} or section in data_ini else None
    except (ValueError, configparser.Error, AttributeError) as exc:
        raise CouldNotJudge(
            f"Cannot read {name}: {exc}", "Fix: repair its configuration before running init."
        ) from exc


def register_marker(name: str, source: str, section: str) -> str:
    """Keep other settings verbatim; change only the existing marker value or add it."""
    match = re.search(r"(?m)^\[" + re.escape(section) + r"\][^\n]*(?:\n|$)", source)
    if match is None:
        # A valid but unconventional TOML table must not be duplicated.
        if name.endswith(".toml"):
            data = tomllib.loads(source)
            branch: object = data
            for part in section.split("."):
                branch = branch.get(part) if isinstance(branch, dict) else None
            if branch is not None:
                raise CouldNotJudge(
                    f"{name} uses a nonstandard spelling of [{section}].",
                    "Fix: use a plain table header, then rerun init.",
                )
        addition = f"\n[{section}]\n"
        source += addition
        return register_marker(name, source, section)
    next_header = re.search(r"(?m)^\[", source[match.end() :])
    end = match.end() + next_header.start() if next_header else len(source)
    body = source[match.end() : end]
    field = re.search(
        r"^[ \t]*markers[ \t]*=[ \t]*",
        body,
        re.MULTILINE | (0 if name.endswith(".toml") else re.IGNORECASE),
    )
    if name.endswith(".toml"):
        data = tomllib.loads(source)
        table = data
        for part in section.split("."):
            table = table[part]
        markers = table.get("markers", [])
        if isinstance(markers, str):
            markers = markers.splitlines()
        if not isinstance(markers, list) or any(not isinstance(m, str) for m in markers):
            raise CouldNotJudge(
                f"{name}: markers must be strings.", "Fix: correct the markers setting."
            )
        if any(re.match(r"^\s*verifies\b", m) for m in markers):
            return source
        value = "markers = " + json.dumps([*markers, MARKER], ensure_ascii=False) + "\n"
        if "markers" in table and field is None:
            raise CouldNotJudge(
                "Cannot safely locate the markers assignment.",
                "Fix: use an unquoted markers key in the pytest table.",
            )
        if field:
            # The first complete TOML value terminates the original assignment, including arrays.
            stop = field.end()
            for line in body[field.end() :].splitlines(keepends=True):
                stop += len(line)
                try:
                    tomllib.loads("markers = " + body[field.end() : stop])
                except ValueError:
                    continue
                break
            body = body[: field.start()] + value + body[stop:]
        else:
            body = value + body
    else:
        ini = configparser.ConfigParser(interpolation=None)
        ini.read_string(source)
        markers = ini.get(section, "markers", fallback="")
        if any(re.match(r"^\s*verifies\b", m) for m in markers.splitlines()):
            return source
        if field:
            line_end = body.find("\n", field.end())
            if line_end < 0:
                body += "\n"
                line_end = len(body) - 1
            body = body[: line_end + 1] + "    " + MARKER + "\n" + body[line_end + 1 :]
        else:
            body = "markers =\n    " + MARKER + "\n" + body
    return source[: match.end()] + body + source[end:]
