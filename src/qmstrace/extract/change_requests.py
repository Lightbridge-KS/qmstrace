"""Read a request's metadata preamble; examples and prose never grant approval."""

import re

from qmstrace.core.baselines import ChangeRequest
from qmstrace.core.model import ID_TOKEN
from qmstrace.extract.fields import FIELD


def read(file: str, request_id: str, text: str) -> tuple[ChangeRequest | None, str | None]:
    """Return a request or a diagnostic. Only metadata before the first prose section counts."""
    fields: dict[str, str] = {}
    title_seen = False
    fence: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(("```", "~~~")):
            mark = line[:3]
            fence = None if fence == mark else mark if fence is None else fence
            continue
        if fence or not line:
            continue
        if line.startswith("# ") and not title_seen and not fields:
            title_seen = True
            token = line[2:].split()[0]
            if ID_TOKEN.fullmatch(token) and token != request_id:
                return None, "heading ID disagrees with the request filename"
            continue
        match = FIELD.match(raw)
        if match is None:
            break
        key, value = match.groups()
        if key not in {"State", "Impacts"}:
            continue
        if key in fields:
            return None, f"duplicate {key} metadata"
        fields[key] = value.strip()
    if not fields.get("State") or "Impacts" not in fields:
        return None, "request metadata needs State and Impacts before its prose sections"
    impacts = [s.strip() for s in fields["Impacts"].split(",")]
    if any(
        not (ID_TOKEN.fullmatch(s) or re.fullmatch(r"[^\s,:]+\.py(?:::[^\s,]+)?", s))
        for s in impacts
    ):
        return None, "Impacts must be a nonempty comma-separated list of item IDs"
    return ChangeRequest(request_id, file, fields["State"], frozenset(impacts)), None
