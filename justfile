# qmstrace — task runner. `just` lists the recipes.

default:
    @just --list

# install the project and its development tools
sync:
    uv sync

# run the tests, with the coverage floor
test:
    uv run pytest -q

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

# build a wheel and prove that the package data is inside it
wheel:
    rm -rf dist
    uv build --wheel --quiet
    uv run python -c "import glob, zipfile; names = zipfile.ZipFile(glob.glob('dist/*.whl')[0]).namelist(); assert 'qmstrace/assets/README.md' in names, names; print('wheel carries the package data')"

# the user manual, served with live reload at http://localhost:8000
manual:
    uv run --isolated --locked --only-group docs zensical serve

# build the user manual strictly — a broken link, anchor or included file fails it
manual-build:
    uv run --isolated --locked --only-group docs zensical build --clean

# the dry gate — everything a pull request must pass; hermetic, no network
dry: lint types test wheel manual-build
