# qmstrace — task runner. `just` lists the recipes.

default:
    @just --list

# install the project and its development tools
sync:
    uv sync

# run the tests, with the coverage floor
test:
    uv run pytest -q
    uv run python tests/check_coverage.py
    node --test tests/browser/*.test.cjs

# check formatting and lint — changes nothing
lint:
    uv run ruff format --check .
    uv run ruff check .

# format and apply safe fixes
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# type check
types:
    uv run mypy

# build each distribution without workspace source overrides
build-wheels:
    uv build --package qmstrace --wheel --no-sources --quiet
    uv build --package qmstrace-lang-csharp --wheel --no-sources --quiet

# network preparation, separate from offline installed-wheel verification
prepare-wheelhouse: build-wheels
    uv run python tests/check_plugin_wheels.py --prepare

# assets, import order, isolated installations and independent plugin replacement
wheel: build-wheels
    uv run python tests/check_wheel.py
    uv run python tests/check_plugin_wheels.py

# the user manual, served with live reload at http://localhost:8000
manual:
    uv run --isolated --locked --only-group docs zensical serve

# build the user manual strictly — a broken link, anchor or included file fails it
manual-build:
    uv run --isolated --locked --only-group docs zensical build --clean

# the dry gate — everything a pull request must pass; hermetic, no network
dry: lint types test wheel manual-build
