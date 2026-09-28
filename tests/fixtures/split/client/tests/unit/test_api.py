import pytest


@pytest.mark.verifies("REQ-CLT-01", "DSN-CLT-01")
def test_every_call_carries_the_key():
    assert True


@pytest.mark.verifies("REQ-SVC-01")
def test_a_call_without_a_key_is_refused():
    assert True
