"""One manifest-first catalog for a workspace invocation; handlers load on demand.

Distribution resources and top-level editable package specs are read without importing
plugin code. Packages are trusted, synchronous Python code, not a sandbox.

Implements: DSN-QMT-17
"""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.metadata as metadata
import json
import platform
import re
import tomllib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType, ModuleType
from urllib.parse import urlparse
from urllib.request import url2pathname

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from qmstrace import __version__
from qmstrace.core.config import BUILTINS, ExtractorDescriptor, ItemType, TraceConfig
from qmstrace.core.errors import ProviderUnavailable as ProviderUnavailable
from qmstrace.core.model import Extracted
from qmstrace.extract.base import FORMS, REGISTRY, IExtractor
from qmstrace.plugins.adapter import adapt, request


class PluginFault(RuntimeError):
    """An identified provider failed execution or violated the public contract."""


@dataclass(frozen=True)
class Provider:
    distribution: str
    version: str
    package: str
    api: int | None
    extractors: tuple[str, ...]
    problems: tuple[str, ...]
    parsers: tuple[tuple[str, str], ...] = ()

    def public(self) -> dict[str, object]:
        return dict(
            distribution=self.distribution,
            version=self.version,
            package=self.package,
            api=self.api,
            extractors=list(self.extractors),
            compatible=not self.problems,
            problems=list(self.problems),
            parser_dependencies=dict(self.parsers),
        )


def _manifest(dist: metadata.Distribution, package: str) -> str:
    """Installed resource first; uv editable via a top-level spec, never find_spec of a child."""
    resource = Path(str(dist.locate_file(f"{package}/plugin.toml")))
    if resource.is_file():
        return resource.read_text(encoding="utf-8")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    if not isinstance(direct, dict) or not isinstance(direct.get("dir_info", {}), dict):
        raise ValueError("invalid editable distribution metadata")
    if direct.get("dir_info", {}).get("editable") is not True:
        raise ValueError("plugin.toml is absent from the installed distribution")
    if not isinstance(direct.get("url"), str):
        raise ValueError("editable source URL must be text")
    url = urlparse(direct["url"])
    if url.scheme != "file" or url.netloc not in ("", "localhost"):
        raise ValueError("editable source is not a local directory")
    base = Path(url2pathname(url.path)).resolve()
    spec = importlib.machinery.PathFinder.find_spec(package)
    if spec is None or spec.origin is None:
        raise ValueError("editable top-level package cannot be located")
    origin = Path(spec.origin).resolve()
    if not origin.is_relative_to(base):
        raise ValueError("editable package resolves outside its distribution source")
    return origin.with_name("plugin.toml").read_text(encoding="utf-8")


class Catalog:
    """Immutable admitted descriptors and a private lazy-handler cache for one invocation."""

    def __init__(self, distributions: Iterable[metadata.Distribution] | None = None) -> None:
        descriptors = dict(BUILTINS)
        self._owners: dict[str, tuple[Provider, str]] = {}
        self._handlers: dict[str, ModuleType] = {}
        self._used: set[str] = set()
        providers: list[Provider] = []
        candidates: dict[str, list[tuple[Provider, str, ExtractorDescriptor]]] = {}
        for dist in distributions if distributions is not None else metadata.distributions():
            for ep in dist.entry_points:
                if ep.group != "qmstrace.extractors":
                    continue
                name = str(canonicalize_name(dist.metadata.get("Name") or "unknown"))
                version = dist.version or "<missing>"
                names: tuple[str, ...] = ()
                api: int | None = None
                declared: dict[str, object] = {}
                entries: dict[str, tuple[str, ExtractorDescriptor]] = {}
                parsers: tuple[tuple[str, str], ...] = ()
                problems: tuple[str, ...] = ()
                try:
                    if not dist.metadata.get("Name") or not dist.version:
                        raise ValueError("distribution name and version are required")
                    Version(version)
                    if not re.fullmatch(r"[A-Za-z_]\w*", ep.value):
                        raise ValueError("entry point must name one top-level package")
                    raw = tomllib.loads(_manifest(dist, ep.value))
                    declared = raw.get("extractors", {})
                    if not isinstance(declared, dict) or not declared:
                        raise ValueError("extractors must be a nonempty table")
                    names = tuple(sorted(declared))
                    api_value = raw.get("api")
                    api = api_value if type(api_value) is int else None
                    if type(raw.get("manifest")) is not int or raw["manifest"] != 1:
                        raise ValueError("unsupported manifest format")
                    if type(api) is not int or api != 1:
                        raise ValueError("unsupported extraction API (host supports 1)")
                    if set(raw) - {"manifest", "api", "extractors", "parser_dependencies"}:
                        raise ValueError("unknown manifest field")
                    requirements = [Requirement(r) for r in dist.requires or ()]
                    host = [r for r in requirements if canonicalize_name(r.name) == "qmstrace"]
                    if len(host) != 1 or not host[0].specifier or host[0].marker is not None:
                        raise ValueError(
                            "distribution must declare an unconditional qmstrace version range"
                        )
                    if not host[0].specifier.contains(Version(__version__), prereleases=True):
                        raise ValueError(
                            "installed host does not satisfy the declared qmstrace dependency"
                        )
                    deps = raw.get("parser_dependencies", [])
                    if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
                        raise ValueError("parser_dependencies must be distribution names")
                    dependency_names = {canonicalize_name(r.name) for r in requirements}
                    if any(canonicalize_name(d) not in dependency_names for d in deps):
                        raise ValueError(
                            "parser dependencies must also be declared in package metadata"
                        )
                    parsers = tuple(
                        sorted((canonicalize_name(d), metadata.version(d)) for d in deps)
                    )
                    for extractor, spec in declared.items():
                        if (
                            not re.fullmatch(r"[a-z][a-z0-9-]*", extractor)
                            or not isinstance(spec, dict)
                            or set(spec)
                            - {
                                "module",
                                "ids",
                                "links",
                                "identity",
                                "scan",
                                "single_link_description",
                            }
                        ):
                            raise ValueError("invalid extractor declaration")
                        module = spec.get("module", "")
                        if (
                            not isinstance(module, str)
                            or not module.startswith(ep.value + ".")
                            or not all(p.isidentifier() for p in module.split("."))
                        ):
                            raise ValueError("handler must be a module inside the declared package")
                        if spec.get("ids") != "derived" or spec.get("links") not in {
                            "named",
                            "single",
                        }:
                            raise ValueError(
                                "API v1 requires derived IDs and named or single links"
                            )
                        for key in ("identity", "scan", "single_link_description"):
                            if not isinstance(spec.get(key, ""), str):
                                raise ValueError(f"{key} must be text")
                        if not spec.get("identity"):
                            raise ValueError("identity description is required")
                        entries[extractor] = (
                            module,
                            ExtractorDescriptor(
                                single_link=spec["links"] == "single",
                                identity=spec["identity"],
                                scan=spec.get("scan", ""),
                                single_link_description=spec.get(
                                    "single_link_description", "an unnamed link"
                                ),
                            ),
                        )
                except (OSError, ValueError, TypeError, metadata.PackageNotFoundError) as error:
                    # Paths and arbitrary exception reprs are not part of metadata inspection.
                    problems = (
                        str(error) if isinstance(error, ValueError) else type(error).__name__,
                    )
                provider = Provider(name, version, ep.value, api, names, problems, parsers)
                providers.append(provider)
                for extractor in names:
                    module, descriptor = entries.get(extractor, ("", ExtractorDescriptor()))
                    if problems:
                        descriptor = replace(descriptor, problem=f"{name}: {'; '.join(problems)}")
                    candidates.setdefault(extractor, []).append((provider, module, descriptor))
        for name, owners in sorted(candidates.items()):
            if name in BUILTINS or len(owners) != 1:
                providers_text = ", ".join(sorted(p.distribution for p, _, _ in owners))
                descriptors[name] = ExtractorDescriptor(
                    problem=f"ambiguous ownership: {providers_text}"
                )
            else:
                provider, module, descriptor = owners[0]
                descriptors[name] = descriptor
                self._owners[name] = (provider, module)
        self.descriptors: Mapping[str, ExtractorDescriptor] = MappingProxyType(descriptors)
        self.providers = tuple(
            sorted(providers, key=lambda p: (p.distribution, p.version, p.package))
        )

    def require(self, name: str) -> None:
        descriptor = self.descriptors.get(name)
        if descriptor is None or descriptor.problem:
            problem = descriptor.problem if descriptor else "no installed provider"
            raise ProviderUnavailable(
                f"Extractor {name}: {problem}.",
                "Fix: install exactly one compatible language wheel into the qmstrace environment "
                "with `uv tool install --with PLUGIN_WHEEL HOST_WHEEL`; "
                "inspect `qmstrace plugins`.",
            )

    def configuration(self, local: str, schema: str | None = None) -> TraceConfig:
        return TraceConfig.parse(local, schema, descriptors=self.descriptors)

    def extractor(self, name: str) -> IExtractor:
        self.require(name)
        if name in REGISTRY:
            self._used.add(name)
            return REGISTRY[name]

        def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
            source = request(path, text, item_type, config)
            return self._call(name, lambda module: adapt(module.extract(source), source))

        return extract

    def form(self, name: str) -> Callable[[str, str], str]:
        self.require(name)
        if name in FORMS:
            return FORMS[name]

        def form(marker: str, target: str) -> str:
            def render(module: ModuleType) -> str:
                result: object = module.form(marker, target)
                if not isinstance(result, str) or not result.strip():
                    raise ValueError("form must return nonempty text")
                return result

            return self._call(name, render)

        return form

    def inspection(self) -> dict[str, object]:
        return {
            "providers": [p.public() for p in self.providers],
            "extractors": {
                name: {
                    "compatible": d.problem is None,
                    "problem": d.problem,
                    "identity": d.identity,
                    "links": "single" if d.single_link else "named",
                    "ids": "authored" if d.authored_ids else "derived",
                }
                for name, d in sorted(self.descriptors.items())
            },
        }

    def toolchain(self) -> dict[str, object]:
        used = {self._owners[n][0].distribution for n in self._used if n in self._owners}
        return {
            "host": {"distribution": "qmstrace", "version": __version__},
            "python": {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
            },
            "providers": [p.public() for p in self.providers if p.distribution in used],
            "extractors": sorted(self._used),
        }

    def _call[T](self, name: str, call: Callable[[ModuleType], T]) -> T:
        self.require(name)
        provider, entry = self._owners[name]
        try:
            if name not in self._handlers:
                handler = importlib.import_module(entry)
                if not callable(getattr(handler, "extract", None)) or not callable(
                    getattr(handler, "form", None)
                ):
                    raise ValueError("handler must expose extract and form")
                self._handlers[name] = handler
            self._used.add(name)
            return call(self._handlers[name])
        except (Exception, SystemExit) as error:
            # Trusted plugin execution is the deliberate exception boundary. No traceback,
            # user paths or raw exception payload is serialized into assessment output.
            raise PluginFault(
                f"Provider {provider.distribution} {provider.version}, extractor {name}: "
                f"{type(error).__name__} during extraction contract execution"
            ) from error
