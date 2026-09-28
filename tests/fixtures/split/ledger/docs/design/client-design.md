# Client — design

## DSN-CLT-01 — Key header
Satisfies: REQ-CLT-01
Assumes: DSN-SVC-01

Every request carries the configured key in its Authorization header; the service's key check
is what refuses a call without one.
