"""Checks the key a call carries.

Implements: DSN-SVC-01
"""


def check(key: str, known: frozenset[str]) -> bool:
    return key in known
