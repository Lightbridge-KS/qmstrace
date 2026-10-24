"""Prove assets ship unchanged and package imports work from the built distribution."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

wheel_path = next(Path("dist").glob("*.whl")).resolve()
with ZipFile(wheel_path) as wheel:
    for asset in Path("src/qmstrace/assets").rglob("*"):
        if asset.is_file():
            name = asset.relative_to("src").as_posix()
            assert wheel.read(name) == asset.read_bytes(), name
    info = next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))
    assert "License-Expression: MIT" in wheel.read(info).decode(), "no license expression"
    license_name = info.replace("METADATA", "licenses/LICENSE")
    assert wheel.read(license_name) == Path("LICENSE").read_bytes(), license_name
print("Wheel carries every setup, skill and browser asset unchanged, and the MIT license.")

# An isolated interpreter outside the checkout cannot fall back to source files or an
# editable installation. Reading directly from the wheel keeps this dry check hermetic.
with TemporaryDirectory() as outside:
    for first in (
        "core.setup",
        "core.graph",
        "core.judge",
        "core.baselines",
        "core.findings",
        "extract.markdown",
        "extract.base",
        "extract.python.module",
        "extract.python.pytest_tests",
        "extract.python_module",
        "extract.pytest_tests",
        "extract.csharp._syntax",
        "extract.csharp.component",
        "extract.csharp.xunit",
        "extract.reports",
        "extract.junit",
        "extract.trx",
        "core.tables",
        "render.text",
        "render.tables",
        "render.graph",
        "render._evidence",
        "workspace",
        "workspace._project",
        "workspace._setup",
        "workspace._baselines",
        "cli",
        "cli._local",
        "cli._ledger",
        "cli._options",
        "cli._outcome",
    ):
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                r"""
import sys
from importlib import import_module
sys.path.insert(0, sys.argv[1])
import_module("qmstrace." + sys.argv[4])
from qmstrace.core import config, setup
from qmstrace.core.config import (
    COPY_BEGIN, COPY_END, EXTRACTORS, SUPPORTED_VERSION, BaselineScope,
    ChangeRequests, CoverageRule, ExternalSource, ItemType, LinkType,
    SchemaForm, Subject, TraceConfig, marked, schema_digest, structural,
)
assert config.__file__.startswith(sys.argv[1] + '/')
assert TraceConfig.__module__ == 'qmstrace.core.config._parse'
local, schema = sys.argv[2:4]
by_path = TraceConfig.parse(local, schema)
copy = setup.copy_schema(local, setup.held_schema(local),
                         setup.schema_block(schema, by_path.project))
assert TraceConfig.parse(copy).schema_digest == by_path.schema_digest
assert TraceConfig.of_schema(schema).rules == by_path.rules
from qmstrace.extract import markdown
from qmstrace.extract.base import REGISTRY, FORMS
from qmstrace.core import graph, judge
from qmstrace.core.baselines import Register
from qmstrace.core.model import Extracted, Item, Link
for package, owners in (
    (markdown, {"_extract": ("CHANGE", "extract", "form")}),
    (setup, {'_guide': ('BEGIN', 'END', 'SKILL_FILE', 'CLAUDE_LINK', 'CLAUDE_LINK_TARGET',
                       'LEGACY_SKILL', 'stanza', 'guide'),
             '_pytest': ('MARKER', 'pytest_section', 'register_marker'),
             '_schema_copy': ('Held', 'Copied', 'ledger_itself', 'before_copy', 'held_schema',
                              'schema_block', 'copy_schema')}),
    (graph, {'_nodes': ('Home', 'Node', 'Surroundings'),
             '_graph': ('TraceGraph', 'Direction', 'Step', 'Closure')}),
    (judge, {'_coverage': ('Form', 'coverage', 'test_backed_requirement'),
             '_baselines': ('resolve_baselines', 'guard'),
             '_suspects': ('suspects',)}),
):
    assert package.__file__.startswith(sys.argv[1] + '/')
    for owner, names in owners.items():
        implementation = import_module(package.__name__ + '.' + owner)
        for name in names:
            assert getattr(package, name) is getattr(implementation, name)
assert REGISTRY['markdown'] is markdown.extract
assert FORMS['markdown'] is markdown.form
text = ("---\nsummary: Ignored\n---\n"
        "## 2.1 **DSN-SVC-01** — Check key {#key}\n"
        "Satisfies: REQ-SVC-01\n"
        "| Satisfies | REQ-SVC-02 |\n"
        "```\n### DSN-SVC-09 — Example\n```\n")
extracted = markdown.extract('design.md', text, by_path.item_types['design_element'], by_path)
assert [(i.id, i.line, i.title) for i in extracted.items] == [('DSN-SVC-01', 4, 'Check key')]
assert [(link.dst, link.line) for link in extracted.links] == [('REQ-SVC-01', 5)]
assert [(s.targets, s.line, s.kind) for s in extracted.strays] == [(('REQ-SVC-02',), 6, 'table')]
assert not extracted.findings and not extracted.leads and not extracted.mentions
assert markdown.form('Satisfies', 'REQ-SVC-01') == '`Satisfies: REQ-SVC-01` under its heading'
from qmstrace.extract import python_module as legacy_module, pytest_tests as legacy_pytest
from qmstrace.extract.python import module, pytest_tests
for legacy, owner, key, names in (
    (legacy_module, module, 'python-module', ('extract', 'form')),
    (legacy_pytest, pytest_tests, 'pytest', ('extract', 'form', 'report_identity')),
):
    assert owner.__file__.startswith(sys.argv[1] + '/')
    assert legacy.__file__.startswith(sys.argv[1] + '/')
    for name in names:
        assert getattr(legacy, name) is getattr(owner, name)
    assert REGISTRY[key] is owner.extract
    assert FORMS[key] is owner.form
source = "'Implements: DSN-SVC-01'\n# Implements: DSN-SVC-02\n"
component = module.extract('src/service.py', source, by_path.item_types['component'], by_path)
assert [i.id for i in component.items] == ['src/service.py']
assert [link.dst for link in component.links] == ['DSN-SVC-01']
assert [s.targets for s in component.strays] == [('DSN-SVC-02',)]
source = ('@pytest.mark.verifies("REQ-SVC-01")\nclass TestKey:\n'
          '    def test_valid(self): pass\n')
read = pytest_tests.extract('tests/unit/test_key.py', source,
                           by_path.item_types['automated_test'], by_path)
assert not read.findings
assert [i.id for i in read.items] == ['tests/unit/test_key.py::TestKey::test_valid']
assert [link.dst for link in read.links] == ['REQ-SVC-01']
assert pytest_tests.report_identity(read.items[0].id) == (
    'tests.unit.test_key.TestKey', 'test_valid')
assert 'pytest' not in sys.modules  # source scanning never imports the test framework
from qmstrace.extract.csharp import component as csharp_file, xunit
assert REGISTRY['csharp-file'] is csharp_file.extract and REGISTRY['xunit'] is xunit.extract
assert FORMS['csharp-file'] is csharp_file.form and FORMS['xunit'] is xunit.form
assert csharp_file.__file__.startswith(sys.argv[1] + '/')
source = '/// Implements: DSN-SVC-01\npublic class Key { }\n'
read = csharp_file.extract('src/Key.cs', source, by_path.item_types['component'], by_path)
assert [link.dst for link in read.links] == ['DSN-SVC-01'] and not read.findings
from importlib.resources import files
starter = files('qmstrace').joinpath('assets/starter.toml').read_text()
for language, extractors in (('python', ('python-module', 'pytest')),
                             ('csharp', ('csharp-file', 'xunit'))):
    tail = files('qmstrace').joinpath(f'assets/items-{language}.toml').read_text()
    joined = (starter + '\n' + tail).replace('__SUBJECT__', 'service').replace('__KEY__', 'SVC')
    types = TraceConfig.parse(joined).item_types
    assert (types['component'].extractor, types['automated_test'].extractor) == extractors
block = setup.stanza(files('qmstrace').joinpath('assets/stanza.md').read_text(), by_path)
guide = setup.guide('Existing guide', block)
assert setup.guide(guide, block) == guide
assert setup.SKILL_FILE in guide
for name, source in (('pytest.ini', '[pytest]\n'),
                     ('pyproject.toml', '[tool.pytest.ini_options]\n')):
    section = setup.pytest_section(name, source)
    assert section is not None
    registered = setup.register_marker(name, source, section)
    assert setup.MARKER in registered
    assert setup.register_marker(name, registered, section) == registered
requirement = Item('REQ-SVC-01', 'requirement', 'srs.md', 1, 'Key required', 'req',
                   {'Category': 'security', 'Origin': 'AGR-1', 'Verify-by': 'test'})
design = Item('DSN-SVC-01', 'design_element', 'design.md', 1, 'Check key', 'dsn')
link = Link(design.id, requirement.id, 'Satisfies', 'design.md', 2)
g, wrong = graph.TraceGraph.build(by_path, [Extracted((requirement, design), (link,))])
assert not wrong
assert g.node(requirement.id).home is graph.Home.LOCAL
assert list(g.forward([requirement.id]).steps) == [design.id]
assert list(g.backward([design.id]).steps) == [requirement.id]
assert g.forward([requirement.id]).direction is graph.Direction.FORWARD
joined = graph.TraceGraph.join(by_path, {'service': g})
assert joined.node(requirement.id).repo == 'service'
assert judge.coverage(by_path, joined)
assert judge.resolve_baselines(by_path, (), {}, frozenset()) == ()
assert judge.guard(by_path, joined.items(), (), frozenset(), Register()) == ((), ())
assert judge.suspects(joined, ()) == ()
from qmstrace.render import text, graph as browser
from qmstrace.render._evidence import evidence
from qmstrace.core.assessment import Assessment, ProjectAssessment, RepoState
from qmstrace.core.results import Report, ReportSource, summarize
assert text.__file__.startswith(sys.argv[1] + '/')
for owner, names in (
    ('text._status', ('status', 'LISTED', 'CATEGORY', 'VERIFY_BY', 'TESTED')),
    ('text._walks', ('thread', 'impact', 'ledger_thread', 'ledger_impact')),
    ('text._checks', ('check', 'ledger_check', 'VIOLATION_HEADING', 'PROJECT_GAP_HEADING')),
    ('text._results', ('results',)),
    ('text._schema', ('rules', 'schema_copies')),
    ('_evidence', ('evidence',)),
):
    implementation = import_module('qmstrace.render.' + owner)
    for name in names:
        assert getattr(text, name) is getattr(implementation, name)
assessment = Assessment(by_path, 'working tree', None, (), g, (), (), (), (), True, ())
project = ProjectAssessment(by_path, (RepoState('service', '.', 'working tree', ()),),
                            joined, (), (), (), Register(), ())
assert browser.evidence is evidence is text.evidence
assert browser.projection(assessment)['evidence'] == text.evidence(assessment)
outputs = (
    text.status(assessment), text.thread(assessment, requirement.id),
    text.impact(assessment, [requirement.id]), text.rules(by_path),
    text.schema_copies(by_path, ()),
    text.results(summarize(assessment, {ReportSource('report.xml', ''): Report()}, {})),
    text.ledger_thread(project, requirement.id), text.ledger_impact(project, [requirement.id]),
)
assert all(isinstance(output, str) and output for output in outputs)
for strict in (False, True):
    for quiet in (False, True):
        assert 'exit 0' in text.check(assessment, strict=strict, quiet=quiet)
        assert 'working trees, not pinned' in text.ledger_check(project, strict=strict, quiet=quiet)
from pathlib import Path
from tempfile import TemporaryDirectory
from qmstrace import workspace
from qmstrace.workspace import Workspace, CONFIG_FILE, SCHEMA_FILE, TreeFactory
from qmstrace.workspace import _workspace, _discovery
assert workspace.__file__.startswith(sys.argv[1] + '/')
assert Workspace is _workspace.Workspace
assert (CONFIG_FILE, SCHEMA_FILE) == ('qmstrace.toml', 'qmstrace.schema.toml')
assert TreeFactory is _discovery.TreeFactory
with TemporaryDirectory() as fixture:
    root = Path(fixture)
    assert Workspace.initialize(root, subject='example', key='EX')
    assert all(line.startswith('unchanged:') for line in Workspace.initialize(root))
    docs = root / 'docs/req'
    docs.mkdir(parents=True)
    (docs / 'example-srs.md').write_text(
        '### REQ-EX-01 — A requirement\nCategory: security\nVerify-by: test\n')
    opened = Workspace.open(docs)
    assessed = opened.assessment()
    assert assessed.graph.node('REQ-EX-01') is not None
    assert not assessed.violations
    assert opened.thread('REQ-EX-01') == assessed
    assert opened.impact(iter(['REQ-EX-01'])) == assessed
    Workspace.save_view(root / 'view.html', '<h1>example</h1>')
    assert (root / 'view.html').read_text() == '<h1>example</h1>'
from importlib.metadata import distribution
from typer.testing import CliRunner
from qmstrace import cli
assert cli.__file__.startswith(sys.argv[1] + '/')
entry = next(e for e in distribution('qmstrace').entry_points
             if e.group == 'console_scripts' and e.name == 'qmstrace')
assert entry.value == 'qmstrace.cli:app'
assert entry.load() is cli.app
for owner, names in (
    ('_app', ('app', 'main')),
    ('_local', ('status', 'thread', 'impact', 'results', 'check', 'rules', 'init', 'graph')),
    ('_ledger', ('ledger', 'copy_schema', 'ledger_check', 'ledger_thread', 'ledger_impact',
                 'ledger_table')),
    ('_options', ('Directory',)),
    ('_outcome', ('outcome', 'EXIT_CODES', 'EXIT_OK', 'EXIT_FAILED',
                  'EXIT_COULD_NOT_JUDGE', 'EXIT_INTERNAL')),
):
    implementation = import_module('qmstrace.cli.' + owner)
    for name in names:
        assert getattr(cli, name) is getattr(implementation, name)
runner = CliRunner()
for command in ((), ('ledger',), *((c.callback.__name__,) for c in cli.app.registered_commands),
                *(('ledger', c.name) for c in cli.ledger.registered_commands)):
    result = runner.invoke(entry.load(), [*command, '--help'], prog_name='qmstrace')
    assert result.exit_code == 0, result.output
    assert result.stdout_bytes and not result.stderr_bytes
assert len(cli.app.registered_commands) == 9 and len(cli.ledger.registered_commands) == 5
assert len(cli.app.registered_groups) == 1
print(f'Wheel package imports and behavior pass in isolation ({sys.argv[4]} first).')
""",
                str(wheel_path),
                Path("tests/fixtures/mini/service/qmstrace.toml").read_text(encoding="utf-8"),
                Path("tests/fixtures/mini/ledger/qmstrace.schema.toml").read_text(encoding="utf-8"),
                first,
            ],
            cwd=outside,
            check=True,
        )
