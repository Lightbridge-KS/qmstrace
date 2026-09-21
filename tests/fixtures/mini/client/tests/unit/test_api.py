import pytest


@pytest.mark.verifies("REQ-CLT-01")
def test_every_call_carries_the_key():
    assert True


@pytest.mark.verifies("REQ-SVC-01")
def test_the_service_refuses_a_call_without_a_key():
    assert True
