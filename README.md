# Strategy Development Lab

## Setup & Upkeep
* Set up the project with `uv venv --python 3.13` and install dev tooling with `uv sync --extra dev`; `uv` will create and manage the local `.venv` for the workspace.
* Install a new runtime dependency with `uv add <package>` or a dev-only dependency with `uv add --dev <package>`; this updates `pyproject.toml` and the lockfile together.
* Run checks with `uv run mypy . && uv run ruff check .`, auto-format using `uv run ruff format .`
* In VS Code, open the folder after `uv venv` so the configured interpreter at `.venv/bin/python` is picked up automatically.

## For Humans Only
* Get started with your favorite codex/claude. "Hi, please read `PROGRAM.md` validate you have everything and get working."

### How it works?

For every iteration the agent will run uv run python -m strategy_dev.backtest which will produce an output like this -

```
sharpe: 2.59
expectancy: 15689.19
cagr: 16.70%
absolute_return: 428.24%
max_drawdown: -18.02%
number_of_trades: 225
win_rate: 30.67%
loss_rate: 69.33%
average_win: 33338.08
average_loss: -7882.94
profit_factor: 1.87
```

Autonomous agent reads these parameters for the backtest on from the output and makes changes to strategy in any way it thinks will improve the CAGR metric.

All the results are logged in a results.tsv which both you and the angent can refer to track progress.