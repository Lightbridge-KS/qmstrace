---
summary: The gateway's requirements, written to be traced.
---

# Gateway — requirements

## 1. Registration

### 1.1 REQ-RCH-01 — Registration under a supplied client ID {#req-registration}
The gateway shall register an agent under the client ID that the agent supplies.

- Category: functional-suitability

#### 1.1.1 Acceptance criteria

| Given | When | Then |
|---|---|---|
| no agent `edge-01` | `edge-01` registers | the list shows `edge-01` |
| `edge-01` registered | `edge-01` registers again | the list still shows one `edge-01` |

### 1.2 **REQ-RCH-02** — Only a caller with the key registers
The gateway shall refuse a registration that carries no valid API key.

- Category: security

#### 1.2.1 Acceptance criteria

- A call with no key, or the wrong one, gets status 401 and registers nothing.

## 2. Summary

| Requirement | Priority |
|---|---|
| REQ-RCH-01 | P0 |
| REQ-RCH-02 | P0 |
