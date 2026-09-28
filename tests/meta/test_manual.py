"""The user manual — what keeps it from drifting from the tool it describes.

The load-bearing claims, each pinned by a test:

1. The findings table the manual shows is rendered from the catalogue, never typed.
2. Every registered command has a reference page — a command nobody can look up is unfinished.
3. Every page opens with its title and then a TL;DR, so a reader decides in five lines.
4. Every page is in the navigation; a page nobody can reach is dead text.
5. A page includes only files that tests own — goldens and fixtures — and each one exists.
   What the tool prints is included, never restated.
"""

import re
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.core.findings import CODES, KINDS

ROOT = Path(__file__).parents[2]
CONTENTS = ROOT / "contents"
TESTS = ROOT / "tests"
MANUAL_GOLDEN = TESTS / "manual"
INCLUDABLE = ("cli/golden/", "manual/", "fixtures/mini/")  # relative to tests/, the base path
SNIPPET = re.compile(r'--8<--\s+"([^"]+)"')
PAGES = sorted(p.relative_to(CONTENTS).as_posix() for p in CONTENTS.rglob("*.md"))


def findings_table() -> str:
    rows = [f"| {code} | {KINDS[code[0]]} | {meaning} |" for code, meaning in sorted(CODES.items())]
    return "\n".join(["| Code | Kind | What is wrong |", "|---|---|---|", *rows]) + "\n"


def nav_pages(entries: list[object]) -> set[str]:
    found: set[str] = set()
    for entry in entries:
        if isinstance(entry, str):
            found.add(entry)
        elif isinstance(entry, dict):
            for value in entry.values():
                found |= nav_pages(value if isinstance(value, list) else [value])
    return found


def test_the_findings_table_is_the_catalogue(golden: Callable[[Path, str], None]) -> None:
    golden(MANUAL_GOLDEN / "findings.md", findings_table())


def test_every_command_has_a_reference_page(commands: list[str]) -> None:
    missing = [
        c for c in commands if not (CONTENTS / "reference" / "commands" / f"{c}.md").is_file()
    ]
    assert not missing, f"commands with no page under contents/reference/commands/: {missing}"


def test_a_groups_page_includes_each_verbs_help(subcommands: dict[str, list[str]]) -> None:
    for group, verbs in subcommands.items():
        page = (CONTENTS / "reference" / "commands" / f"{group}.md").read_text(encoding="utf-8")
        missing = [v for v in verbs if f'--8<-- "cli/golden/help-{group}-{v}.txt"' not in page]
        assert not missing, f"{group}.md does not include the help of: {missing}"


@pytest.mark.parametrize("page", PAGES)
def test_a_page_opens_with_its_title_and_a_tldr(page: str) -> None:
    lines = [line for line in (CONTENTS / page).read_text(encoding="utf-8").splitlines() if line]
    assert lines[0].startswith("# "), f"{page}: the first line is not an H1 title"
    assert lines[1] == '!!! abstract "TL;DR"', f"{page}: the title is not followed by the TL;DR"


def test_every_page_is_in_the_navigation() -> None:
    config = tomllib.loads((ROOT / "zensical.toml").read_text(encoding="utf-8"))
    listed = nav_pages(config["project"]["nav"])
    assert set(PAGES) == listed, (
        f"not in nav: {sorted(set(PAGES) - listed)}; in nav, no page: {sorted(listed - set(PAGES))}"
    )


@pytest.mark.parametrize("page", PAGES)
def test_a_page_includes_only_files_that_tests_own(page: str) -> None:
    for target in SNIPPET.findall((CONTENTS / page).read_text(encoding="utf-8")):
        assert target.startswith(INCLUDABLE), f"{page} includes {target}, outside {INCLUDABLE}"
        assert (TESTS / target).is_file(), f"{page} includes {target}, which does not exist"


def test_the_copy_example_is_what_the_command_writes(
    golden: Callable[[Path, str], None], embed: Callable[..., str]
) -> None:
    mini = TESTS / "fixtures" / "mini"
    local = (mini / "service" / "qmstrace.toml").read_text(encoding="utf-8")
    schema = (mini / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
    golden(MANUAL_GOLDEN / "copy-example.toml", embed(local, schema))
