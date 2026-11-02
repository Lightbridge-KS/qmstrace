"""Metadata-only provider inspection as readable terminal text.

Implements: DSN-QMT-17
"""


def report(data: dict[str, object]) -> str:
    lines = ["Installed extractor providers"]
    providers = data["providers"]
    assert isinstance(providers, list)
    if not providers:
        lines.append("  No external providers installed.")
    for provider in providers:
        state = "compatible" if provider["compatible"] else "rejected"
        lines.append(
            f"  {provider['distribution']} {provider['version']} · API {provider['api']} · {state}"
        )
        for problem in provider["problems"]:
            lines.append(f"    problem: {problem}")
    lines.append("Extractors")
    extractors = data["extractors"]
    assert isinstance(extractors, dict)
    for name, descriptor in extractors.items():
        problem = descriptor["problem"]
        lines.append(f"  {name}: {problem or descriptor['identity']}")
    lines.append("Manifest inspection only; handler execution and source evidence not assessed.")
    return "\n".join(lines)
