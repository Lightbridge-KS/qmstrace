"""Pure semantic ANSI formatting; terminal policy belongs to the CLI.

Implements: DSN-QMT-12
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Style:
    """Presentation selected by a caller; plain is always the default."""

    enabled: bool = False

    def paint(self, text: str, code: str) -> str:
        return f"\x1b[{code}m{text}\x1b[0m" if self.enabled and text else text

    def heading(self, text: str) -> str:
        return self.paint(text, "1;36")

    def warning(self, text: str) -> str:
        return self.paint(text, "33")

    def error(self, text: str) -> str:
        return self.paint(text, "31")

    def location(self, text: str) -> str:
        return self.paint(text, "2")

    def verdict(self, verdict: str, *, width: int = 0) -> str:
        text = verdict.ljust(width)
        code = "31" if verdict == "fail" else "32" if verdict == "pass" else "33"
        return self.paint(text, code)


PLAIN = Style()
