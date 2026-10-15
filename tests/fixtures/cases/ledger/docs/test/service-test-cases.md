# Service — test cases

The planned test cases for the service. `TC-SVC-NN.m` is test case *m* of design element
`DSN-SVC-NN`; what each verifies is the line under it. Several automated tests may run one
test case, which passes only when all of them pass.

## TC-SVC-01.1 — A call without a valid key is refused
verifies: REQ-SVC-01

A call with no key, and a call with a wrong one, are each answered 401.

## TC-SVC-01.2 — The key check runs before any handler
verifies: DSN-SVC-01

No handler sees a call the key check has refused.

## TC-SVC-02.1 — A restart keeps every field of a record
verifies: DSN-SVC-02

A record read after a restart equals the record written before it.

## TC-SVC-02.2 — A record written during a restart is not lost
verifies: REQ-SVC-02

Planned; no automated test runs it yet.
