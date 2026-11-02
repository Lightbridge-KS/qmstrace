---
summary: ADR-0014 — Python module and pytest extraction move into an explicitly installed package using API v1; legacy internal imports are removed under accepted CR-008.
read_when:
  - changing Python provider ownership, setup admission or legacy extractor imports
---

# ADR-0014 — Explicitly installed Python extraction

- **Status:** accepted 2026-11-02; implemented; local gates pass, native Windows candidate verification pending
- **Decided by:** developer-manager through the accepted plan and CR-008
- **Amends:** ADR-0013's bundled-Python boundary and the blueprint's Python compatibility facades
- **Change control:** accepted CR-008, requirements 02 and 12

## Context

The C# package uses a manifest-first public API, while Python still uses internal configuration
and finding objects. Keeping a built-in language alongside an external equivalent would
preserve two execution paths and tie Python extraction changes to host releases.

## Decision

Use one `qmstrace-lang-python` package for `python-module` and `pytest`, registered through
the existing API v1. The host keeps only Markdown in its built-in registry. Python installation
is explicit, even for the default starter; setup refuses before writing when its provider
is unavailable. Host setup still owns pytest marker registration and transactional writes.

Remove `qmstrace.extract.python`, `qmstrace.extract.python_module` and
`qmstrace.extract.pytest_tests`. Their former internal signatures are not forwarded.
CLI extractor names and trace configuration retain their meaning. Python source is parsed
with stdlib `ast`, never imported; pytest is not a runtime dependency. Digests preserve the
existing AST representation, so runtime version remains part of reproducibility evidence.

Include the migration in unpublished host 0.4.0. Python and C# plugins each prepare 0.1.0,
with independent future versions and release tags. The host has neither as a runtime dependency.

The accepted compatibility correction allows duplicate extracted IDs through the adapter
for host V01 validation, preserving declarations and locations. It changes no API fields;
all other result validation remains in force. Duplicate provider ownership still refuses.

## Consequences

Consumers install the Python wheel into the host environment. Development installs both
workspace members. All three production packages retain separate coverage floors and
isolated wheel checks. Source-path moves change derived trace identities; suspects require
review. Publication and consumer migration remain separate operations.

## Rejected alternatives

- A host runtime dependency on Python extraction would hide the explicit installation boundary.
- Temporary legacy wrappers would keep unsupported internal signatures and host-language coupling.
- Separate module/pytest packages would split shared syntax and digest policy without a release need.
- Setup hooks or a new API major are unnecessary for the text extraction boundary.

## Verification

The [tracker](../progress/python-extractor-plugin.md) records current evidence and remaining
platform acceptance. The [extensibility design](../design/extensibility-architecture.md)
owns the shared mechanism; this decision does not expand its trust or execution model.
