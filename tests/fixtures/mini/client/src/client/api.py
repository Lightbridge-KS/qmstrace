"""Calls the service."""


def headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Key {key}"}
