---
summary: The service's requirement items — the fixture project's reference example.
read_when: Before writing or changing a requirement of the service.
---

# Service — requirements

Each item derives from a clause of the project's agreement (`AGR-N`), which is in the ledger.

## Keys

### REQ-SVC-01 — A call carries a key
The service shall refuse, with status 401, a call that carries no valid key.

- Category: security
- Origin: AGR-1
- Verify-by: test

## Records

### REQ-SVC-02 — Records survive a restart
The service shall keep every record it has accepted across a restart.

- Category: reliability
- Origin: AGR-2, AGR-3
- Verify-by: test

### REQ-SVC-03 — The record format is written down
The service shall document the format of a stored record.

- Category: maintainability
- Origin: AGR-3
- Verify-by: inspection

The form of an item, shown in a fence, declares nothing:

```markdown
### REQ-SVC-99 — An example inside a fence
```
