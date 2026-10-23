---
summary: ADR-0009 — status and results distinguish test-backed requirements by applicable incoming verifies coverage rules, while linked test outcomes remain evidence rather than approval of another verification method.
read_when:
  - changing how status or results groups requirements by verification method
  - adding a Verify-by value or changing a requirement coverage rule
  - interpreting linked test outcomes for inspection, analysis or demonstration
---

# ADR-0009 — Group verification by applicable rules

- **Status:** accepted, 2026-10-23
- **Amends:** [surface architecture](../design/surface-architecture.md) status and results display contract
- **Decided by:** the developer, 2026-10-23, for issue #57

## Context

`status` listed any `Verify-by` value other than `test` apart, while `results` listed apart
only `inspection` and `analysis`. A new method such as `demonstration` therefore appeared
outside tested requirements in one command but received a requirement verdict in the other.

## Decision

A requirement is displayed as test-backed only when its valid, declared `Verify-by` value
matches at least one coverage rule requiring an incoming `verifies` link for requirements.
The whole `where` condition must match. Several applicable rules have the same effect; the
rule code has no special meaning. A missing or invalid method stays outside the test-backed
display and retains its V05 validation finding. With no applicable rule, the requirement is
listed apart even when a test links to it.

`results` still computes and shows linked test outcomes for every requirement. In the apart
section they are labelled test evidence only: a passing test does not establish completion or
approval of an inspection, analysis or demonstration. Coverage gaps, verdict aggregation,
exit codes and the versioned `ledger table` report-verdict cells are unchanged.

## Rejected alternatives

- **Hardcode additional method names.** A future schema would recreate the disagreement.
- **Recognize the rule by `G02`.** Rule codes are configurable identifiers, not method
  semantics; another rule may require the same link for a different method.
- **Infer the method from a test link.** A link records test evidence, not a decision about how
  a requirement is verified.
