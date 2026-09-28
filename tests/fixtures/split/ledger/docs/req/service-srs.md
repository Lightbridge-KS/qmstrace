# Service — requirements

Kept in the project's ledger. Each item derives from a clause of the agreement beside it.

### REQ-SVC-01 — A call carries a key
The service shall refuse, with status 401, a call that carries no valid key.

- Category: security
- Origin: AGR-1
- Verify-by: test

### REQ-SVC-02 — Records survive a restart
The service shall keep every record it has accepted across a restart.

- Category: reliability
- Origin: AGR-2
- Verify-by: test
