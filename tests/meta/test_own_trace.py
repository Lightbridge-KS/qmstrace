"""qmstrace traces itself — what `qmstrace init` installed here must equal what the package ships.

The load-bearing claims, each pinned by a test:

1. The skill copy under `.qmstrace/skill/` equals the packaged skill. A copy that drifts makes
   `init` refuse, and an agent in this repo reads guidance the tool no longer gives.
2. The block in `AGENTS.md` is the stanza this repo's configuration renders — running `init`
   again would change nothing.
"""

from importlib.resources import files
from pathlib import Path

from qmstrace.core import setup
from qmstrace.core.config import TraceConfig

ROOT = Path(__file__).parents[2]
ASSETS = files("qmstrace").joinpath("assets")
RERUN = "run `uv run qmstrace init` and commit what it changes."


def test_the_installed_skill_is_the_packaged_one() -> None:
    installed = (ROOT / ".qmstrace" / "skill" / "SKILL.md").read_text(encoding="utf-8")
    packaged = ASSETS.joinpath("skill/SKILL.md").read_text(encoding="utf-8")
    assert installed == packaged, (
        "the skill copy differs from the packaged skill. "
        f"Fix: keep any local edit elsewhere, remove .qmstrace/skill/SKILL.md, then {RERUN}"
    )


def test_the_agent_guide_carries_the_current_stanza() -> None:
    config = TraceConfig.parse((ROOT / "qmstrace.toml").read_text(encoding="utf-8"))
    block = setup.stanza(ASSETS.joinpath("stanza.md").read_text(encoding="utf-8"), config)
    guide = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert setup.guide(guide, block) == guide, f"AGENTS.md carries a stale stanza. Fix: {RERUN}"
