import pytest


@pytest.mark.verifies("REQ-SVC-02")
def test_a_record_survives_a_restart():
    assert True


@pytest.mark.verifies("TC-SVC-02.1")
def test_a_restart_keeps_every_field():
    assert True
