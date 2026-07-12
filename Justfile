# bbugyi-toolong task runner

venv_dir := ".venv"
venv_bin := venv_dir / "bin"

default:
    @just --list

_venv:
    @[ -x {{ venv_bin }}/python ] || uv venv --python 3.10 {{ venv_dir }}

install: _venv
    uv pip install --python {{ venv_bin }}/python -e ".[dev]"

fmt: install
    {{ venv_bin }}/ruff format src tests
    {{ venv_bin }}/ruff check --fix src tests

fmt-check: install
    {{ venv_bin }}/ruff format --check src tests

lint: install
    {{ venv_bin }}/ruff check src tests
    {{ venv_bin }}/mypy

[positional-arguments]
test *args: install
    {{ venv_bin }}/pytest "$@"

check: fmt-check lint test
