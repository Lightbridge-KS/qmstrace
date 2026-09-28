"""Calls the service, with the configured key.

Implements: DSN-CLT-01
"""


def headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Key {key}"}
