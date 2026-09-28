# Service — design

## DSN-SVC-01 — Key check
Satisfies: REQ-SVC-01

Every call passes the key check before any handler runs.

## DSN-SVC-02 — Record store
Satisfies: REQ-SVC-02
Assumes: DSN-SVC-01

A record is on disk before the call that sent it returns.
