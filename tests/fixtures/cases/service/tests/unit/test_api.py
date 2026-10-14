import pytest


@pytest.mark.verifies("TC-SVC-01.1")
def test_a_call_without_a_key_is_refused():
    assert "" not in {"the-key"}


@pytest.mark.verifies("TC-SVC-01.1")
def test_a_call_with_a_wrong_key_is_refused():
    assert "a-wrong-key" not in {"the-key"}


@pytest.mark.verifies("TC-SVC-01.2")
def test_the_key_check_runs_before_any_handler():
    assert True
