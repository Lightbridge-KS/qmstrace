"""The one way a run says it could not judge."""


class CouldNotJudge(Exception):
    """The repo could not be judged at all — as opposed to being judged and found wanting.

    Raised for a missing or invalid configuration, the wrong kind of repo, an unknown ID, an
    unreadable report, or a shallow clone where baselines are configured. A problem *in* the
    user's repo is never this: it is a finding, and findings are data.

    Parameters
    ----------
    what
        What stopped the run.
    next_move
        What the reader should do about it. Every message that reaches an agent says so.
    """

    def __init__(self, what: str, next_move: str) -> None:
        super().__init__(f"{what} {next_move}")
        self.what = what
        self.next_move = next_move
