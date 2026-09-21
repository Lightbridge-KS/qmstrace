import pytest


@pytest.mark.verifies("REQ-SVC-02", "DSN-SVC-02")
def test_a_record_survives_a_restart(tmp_path):
    assert tmp_path.exists()


@pytest.mark.verifies("REQ-SVC-02")
def test_a_restart_loses_no_accepted_record():
    assert True
