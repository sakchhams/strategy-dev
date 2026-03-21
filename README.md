# Strategy Development Lab

## Setup & Upkeep
* Set up the project with `uv venv --python 3.13` and install dev tooling with `uv sync --extra dev`; `uv` will create and manage the local `.venv` for the workspace.
* Install a new runtime dependency with `uv add <package>` or a dev-only dependency with `uv add --dev <package>`; this updates `pyproject.toml` and the lockfile together.
* Run checks with `uv run mypy . && uv run ruff check .`, auto-format using `uv run ruff format .`
* In VS Code, open the folder after `uv venv` so the configured interpreter at `.venv/bin/python` is picked up automatically.

## For Humans Only
* Get started with your favorite codex/claude. "Hi, please read `PROGRAM.md` validate you have everything and get working."