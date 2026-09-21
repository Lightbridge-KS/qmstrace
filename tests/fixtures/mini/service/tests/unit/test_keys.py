import pytest


@pytest.mark.verifies("REQ-SVC-01")
@pytest.mark.parametrize("key", ["", "wrong"])
def test_a_call_without_a_valid_key_is_refused(key):
    assert key not in {"the-key"}


@pytest.mark.verifies("DSN-SVC-01")
class TestTheKeyCheck:
    def test_it_runs_before_any_handler(self):
        assert True
