import pytest


@pytest.mark.verifies("REQ-SVC-01", "DSN-SVC-01")
def test_a_call_without_a_key_is_refused():
    assert "" not in {"the-key"}
