"""The shipped language implementation consumes only the public host contract."""

import pytest
from qmstrace_lang_csharp import component, xunit

from qmstrace.plugin_api.v1 import Extraction, ExtractRequest


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_public_text_contract_preserves_file_and_report_identities():
    component_request = ExtractRequest(
        "/// Implements: DSN-SVC-01\npublic class C {}",
        "src/C.cs",
        "component",
        markers=("Implements",),
        permitted_markers=("Implements",),
    )
    result = component.extract(component_request)
    assert isinstance(result, Extraction)
    assert result.items[0].id == "src/C.cs"
    assert result.links[0].dst == "DSN-SVC-01"
    test_request = ExtractRequest(
        'public class C { [Fact(DisplayName="REQ-SVC-01 works")] public void Works() {} }',
        "tests/unit/C.cs",
        "automated_test",
        ("unit",),
        ("verifies",),
        ("verifies",),
    )
    found = xunit.extract(test_request)
    assert found.items[0].id == "tests/unit/C.cs::C::Works"
    assert found.items[0].runs_as == (("C", "Works"),)
    assert found.links[0].dst == "REQ-SVC-01"
