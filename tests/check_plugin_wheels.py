"""Offline installed-wheel acceptance, run from the repository root after wheelhouse prep.

The environment has no checkout on its import path. A fixture successor of the actual
C# wheel proves plugin-only replacement; it is not evidence for an older released version.
Results and exact artifacts/environments are written to dist/compatibility-<platform>.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WHEELS = DIST / "wheelhouse"


def run(*args, cwd, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {args[0]}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    host_version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    plugin_version = tomllib.loads(
        (ROOT / "packages/qmstrace-lang-csharp/pyproject.toml").read_text()
    )["project"]["version"]

    def successor_version(version):
        major, minor, patch = version.split(".")
        return f"{major}.{minor}.{int(patch) + 1}.dev0"

    plugin_successor_version = successor_version(plugin_version)
    host_successor_version = successor_version(host_version)
    host = DIST / f"qmstrace-{host_version}-py3-none-any.whl"
    plugin = DIST / f"qmstrace_lang_csharp-{plugin_version}-py3-none-any.whl"
    if "--prepare" in sys.argv:
        run(
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "--dest",
            str(WHEELS),
            str(host),
            str(plugin),
            "uv_build>=0.11.8,<0.12.0",
            cwd=ROOT,
        )
        for own_wheel in WHEELS.glob("qmstrace*.whl"):
            own_wheel.unlink()  # products are always passed explicitly, never resolved here
        print("Dependency wheelhouse prepared.")
        return
    assert WHEELS.is_dir(), "prepare dist/wheelhouse first; see just prepare-wheelhouse"
    for wheel, package in [(host, "qmstrace"), (plugin, "qmstrace_lang_csharp")]:
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            meta = archive.read(
                next(n for n in names if n.endswith(".dist-info/METADATA"))
            ).decode()
            assert f"{package}/py.typed" in names
            assert "License-Expression: MIT" in meta
            assert any(n.endswith("/licenses/LICENSE") for n in names)
            if package == "qmstrace":
                assert "Requires-Dist: tree-sitter" not in meta
                assert not any("/extract/csharp/" in n for n in names)
            else:
                assert "Requires-Dist: qmstrace>=" in meta
                assert "Requires-Dist: tree-sitter" in meta
                assert f"{package}/plugin.toml" in names
    with tempfile.TemporaryDirectory(prefix="qmstrace-wheels-") as temp:
        outside = Path(temp)
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"PYTHONPATH", "QMSTRACE_WORKSPACE", "VIRTUAL_ENV"}
        }
        env.update(
            HOME=str(outside),
            USERPROFILE=str(outside),
            UV_OFFLINE="1",
            UV_NO_INDEX="1",
            UV_FIND_LINKS=str(WHEELS),
        )
        venv = outside / "venv"
        run("uv", "venv", "--python", sys.executable, str(venv), cwd=outside, env=env)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

        def install(*wheels):
            run(
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-index",
                "--find-links",
                str(WHEELS),
                *map(str, wheels),
                cwd=outside,
                env=env,
            )

        def probe(code):
            return run(str(python), "-I", "-c", code, cwd=outside, env=env)

        install(host)
        probe("""import importlib.util
from pathlib import Path
from typer.testing import CliRunner
from qmstrace.cli import app
assert importlib.util.find_spec('tree_sitter') is None
assert importlib.util.find_spec('qmstrace_lang_csharp') is None
root = Path('host-only'); root.mkdir()
r = CliRunner().invoke(app, ['-C', str(root), 'init', '--language', 'csharp'])
assert r.exit_code == 2, r.output
assert not list(root.iterdir())
r = CliRunner().invoke(app, ['-C', str(root), 'init', '--language', 'python'])
assert r.exit_code == 0, r.output
assert CliRunner().invoke(app, ['-C', str(root), 'status']).exit_code == 0
""")
        install(plugin)
        probe("""import sys
from qmstrace.plugins.catalog import Catalog
catalog = Catalog()
assert catalog.providers[0].problems == (), catalog.inspection()
assert 'qmstrace_lang_csharp' not in sys.modules
assert 'tree_sitter' not in sys.modules
""")
        code = """import json, hashlib
from pathlib import Path
from qmstrace.plugin_api.v1 import ExtractRequest
from qmstrace_lang_csharp import component, xunit
from qmstrace.workspace import Workspace
from dataclasses import asdict
source = '/// Implements: DSN-SVC-01\\npublic class Key {}'
request = ExtractRequest(source, 'src/Key.cs', 'component',
    markers=('Implements',), permitted_markers=('Implements',))
found = component.extract(request)
assert found.links[0].dst == 'DSN-SVC-01'
assert found.items[0].id == 'src/Key.cs'
source = '[Fact(DisplayName = "REQ-SVC-01 works")] public void Works() {}'
tests = xunit.extract(ExtractRequest('public class Tests {' + source + '}',
    'tests/unit/Test.cs', 'automated_test', ('unit',), ('verifies',), ('verifies',)))
assert tests.items[0].runs_as == (('Tests','Works'),)
root = Path('csharp'); root.mkdir(exist_ok=True)
if not (root / 'qmstrace.toml').exists(): Workspace.initialize(root, language='csharp')
(root / 'src').mkdir(exist_ok=True)
(root / 'src/Key.cs').write_text('public class Key {}')
assert Workspace.open(root).assessment().toolchain['providers']
print(json.dumps([asdict(found), asdict(tests)], sort_keys=True))
"""
        # A separately built package adds a name absent from the host's registration.
        fixture = outside / "fixture"
        fixture_package = fixture / "src/wheel_fixture"
        fixture_package.mkdir(parents=True)
        (fixture_package / "__init__.py").write_text("")
        (fixture / "pyproject.toml").write_text(
            "[project]\n"
            'name = "wheel-fixture"\n'
            'version = "1.0.0"\n'
            'requires-python = ">=3.13"\n'
            'dependencies = ["qmstrace>=0.4.0"]\n'
            '[project.entry-points."qmstrace.extractors"]\n'
            'fixture = "wheel_fixture"\n'
            "[build-system]\n"
            'requires = ["uv_build>=0.11.8,<0.12.0"]\n'
            'build-backend = "uv_build"\n'
        )
        (fixture_package / "plugin.toml").write_text(
            "manifest=1\n"
            "api=1\n"
            "[extractors.wheel-fixture]\n"
            'module="wheel_fixture.handler"\n'
            'ids="derived"\n'
            'links="named"\n'
            'identity="ID: source path"\n'
        )
        (fixture_package / "handler.py").write_text(
            "from qmstrace.plugin_api.v1 import Extraction, Item, text_digest\n"
            "\n"
            "def extract(request):\n"
            "    return Extraction(items=(Item(request.path, request.item_type, request.path, 1,\n"
            '        "fixture", text_digest(request.text)),))\n'
            "\n"
            "def form(marker, target):\n"
            '    return marker + ": " + target\n'
        )
        run(
            "uv",
            "build",
            "--wheel",
            "--no-sources",
            "--out-dir",
            str(outside / "fixture-built"),
            str(fixture),
            cwd=outside,
            env=env,
        )
        fixture_wheel = next((outside / "fixture-built").glob("*.whl"))
        install(fixture_wheel)
        probe("""from qmstrace.plugins.catalog import Catalog
catalog = Catalog()
catalog.require('wheel-fixture')
raw = '''version=1
[schema]
version=1
project="FIX"
[schema.item_types.component]
[items.component]
extractor="wheel-fixture"
files=["*.txt"]
'''
config = catalog.configuration(raw)
found = catalog.extractor('wheel-fixture')(
    'x.txt', 'fixture', config.item_types['component'], config)
assert found.items[0].id == 'x.txt'
""")
        before = probe(code)
        host_hash = sha(host)
        host_install_hash = probe(
            "import hashlib, qmstrace.plugin_api.v1 as a; from pathlib import Path; "
            "print(hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest())"
        ).strip()
        environment_before = json.loads(
            run(
                "uv",
                "pip",
                "list",
                "--python",
                str(python),
                "--format",
                "json",
                cwd=outside,
                env=env,
            )
        )
        # Build a fixture successor independently of workspace overrides and host source.
        source = outside / "successor"
        import shutil

        shutil.copytree(
            ROOT / "packages/qmstrace-lang-csharp",
            source,
            ignore=shutil.ignore_patterns("__pycache__", ".venv", "dist"),
        )
        manifest = source / "pyproject.toml"

        previous = tomllib.loads(manifest.read_text())["project"]["version"]
        manifest.write_text(
            manifest.read_text().replace(
                f'version = "{previous}"', f'version = "{plugin_successor_version}"'
            )
        )
        run(
            "uv",
            "build",
            "--wheel",
            "--no-sources",
            "--out-dir",
            str(outside / "built"),
            str(source),
            cwd=outside,
            env=env,
        )
        successor = next((outside / "built").glob("*.whl"))
        install(successor)
        after = probe(code)
        assert before == after
        assert sha(host) == host_hash
        assert (
            probe(
                "import hashlib, qmstrace.plugin_api.v1 as a; from pathlib import Path; "
                "print(hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest())"
            ).strip()
            == host_install_hash
        )
        environment_after = json.loads(
            run(
                "uv",
                "pip",
                "list",
                "--python",
                str(python),
                "--format",
                "json",
                cwd=outside,
                env=env,
            )
        )
        delta = {v["name"] for v in environment_after if v not in environment_before}
        assert delta == {"qmstrace-lang-csharp"}, delta
        # Fixture host successor, retaining the original plugin. This is mechanism
        # evidence only: neither fixture successor is a released compatibility baseline.
        host_source = outside / "host-successor"
        host_source.mkdir()
        shutil.copytree(ROOT / "src", host_source / "src")
        shutil.copy(ROOT / "LICENSE", host_source / "LICENSE")
        import re

        host_manifest = (
            (ROOT / "pyproject.toml")
            .read_text()
            .replace(f'version = "{host_version}"', f'version = "{host_successor_version}"')
        )
        host_manifest = re.sub(
            r"\[tool\.uv\.(?:workspace|sources)\][\s\S]*?(?=\n\[|\Z)", "", host_manifest
        )
        (host_source / "pyproject.toml").write_text(host_manifest)
        run(
            "uv",
            "build",
            "--wheel",
            "--no-sources",
            "--out-dir",
            str(outside / "host-built"),
            str(host_source),
            cwd=outside,
            env=env,
        )
        host_successor = next((outside / "host-built").glob("*.whl"))
        install(plugin)
        plugin_hash_code = (
            "import hashlib; from pathlib import Path; "
            "from qmstrace_lang_csharp import component; "
            "print(hashlib.sha256(Path(component.__file__).read_bytes()).hexdigest())"
        )
        plugin_hash = probe(plugin_hash_code)
        install(host_successor)
        assert probe(plugin_hash_code) == plugin_hash
        assert probe(code) == before
        host_update_environment = json.loads(
            run(
                "uv",
                "pip",
                "list",
                "--python",
                str(python),
                "--format",
                "json",
                cwd=outside,
                env=env,
            )
        )
        tool_env = {
            **env,
            "UV_TOOL_DIR": str(outside / "tools"),
            "UV_TOOL_BIN_DIR": str(outside / "tool-bin"),
        }
        constraints = outside / "environment.constraints.txt"
        constraints.write_text(
            run(
                "uv",
                "pip",
                "freeze",
                "--python",
                str(python),
                "--exclude",
                "qmstrace",
                "--exclude",
                "qmstrace-lang-csharp",
                "--exclude",
                "wheel-fixture",
                cwd=outside,
                env=env,
            )
        )
        for wheel in (plugin, successor, plugin):
            run(
                "uv",
                "tool",
                "install",
                "--force",
                "--python",
                sys.executable,
                "--constraints",
                str(constraints),
                "--with",
                str(wheel),
                str(host),
                cwd=outside,
                env=tool_env,
            )
            command = outside / "tool-bin" / ("qmstrace.exe" if os.name == "nt" else "qmstrace")
            inspection = json.loads(
                run(str(command), "plugins", "--json", cwd=outside, env=tool_env)
            )
            assert inspection["data"]["providers"][0]["compatible"]
            expected_version = plugin_successor_version if wheel == successor else plugin_version
            assert inspection["data"]["providers"][0]["version"] == expected_version
        result = {
            "platform": platform.system(),
            "python": platform.python_version(),
            "host_wheel": {"name": host.name, "sha256": host_hash},
            "plugin_wheel": {"name": plugin.name, "sha256": sha(plugin)},
            "fixture_successor": {"name": successor.name, "sha256": sha(successor)},
            "fixture_host_successor": {"name": host_successor.name, "sha256": sha(host_successor)},
            "host_update_environment": host_update_environment,
            "host_api_file_sha256": host_install_hash,
            "environment_before": environment_before,
            "environment_after": environment_after,
            "wheelhouse": [
                {"name": p.name, "sha256": sha(p)} for p in sorted(WHEELS.glob("*.whl"))
            ],
            "checks": [
                "unchanged-plugin-host-update",
                "tool-install-upgrade-rollback",
                "new-fixture-wheel",
                "host-only",
                "no-import-discovery",
                "paired-wheels",
                "unchanged-host-plugin-update",
            ],
            "released_matrix": {
                "oldest-released-compatible-host": "UNVERIFIED: no API v1 host released",
                "previous-released-plugin": "UNVERIFIED: first plugin release",
            },
        }
        (DIST / f"compatibility-{platform.system().lower()}.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        print("Installed-wheel compatibility passed; only the plugin changed in the update.")


if __name__ == "__main__":
    main()
