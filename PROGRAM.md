# Auto Strategy Development

This is an experiment to have an LLM develop and improve a trading strategy iteratively.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autostratdev/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autostratdev/<tag>` from current master.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `src/strategy_dev/data.py` — fixed constants, data prep, bookeeping logic. DO NOT MODIFY.
   - `src/strategy_dev/backtest.py` — the file you modify. Strategy logic, timeframe, what indicators you'd like to use etc.
4. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
5. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment runs on a backtest. You launch it simply as: `uv run python -m strategy_dev.backtest`.

**What you CAN do:**
- Modify `src/strategy_dev/backtest.py` — this is the only file you edit. Everything is fair game: strategy logic, timeframe, what indicators to use, etc.

**What you CANNOT do:**
- Modify `src/strategy_dev/data.py`. It is read-only. It contains core logic for loading data, and ensuring trades are placed and executed fairly.
- Modify the evaluation harness. The output from `print_metrics` function in `data.py` is the ground truth metric.

**The goal is simple: get the maximum CAGR.** Everything is fair game: change the strategy, the indicators, the windows, the timeframe. The only constraint is that the code runs without crashing and output `print_metrics` to stdout.

**Volatility criterion**: All else being equal, simpler is better. A small improvement that adds ugly max drawdowns is not worth it. Conversely, improving sharpe and getting equal or better result is a great outcome — that's a volatility win. When evaluating whether to keep a change, weigh the max_drawdowns against the cagr improvement magnitude. A 1% CAGR improvement that adds 10% extra max drawdown? Not worth it. A 10% CAGR improvement from extra 5% drawdowns? Definitely keep. An improvement of ~0 but lower max_drawdown? Keep.

**The first run**: Your very first run should always be to establish the baseline, so you will run the backtesting script as is.

## Output format

Once the script finishes it prints a summary like this:

```
---
sharpe: 0.88
expectancy: 5590.61
cagr: 19.19%
absolute_return: 600.52%
max_drawdown: -24.34%
number_of_trades: 2434
win_rate: 38.09%
loss_rate: 61.91%
average_win: 7987.37
average_loss: -4116.29
profit_factor: 1.49
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 5 columns:

```
commit	cagr	max_drawdown	status	description
```

1. git commit hash (short, 7 chars)
2. cagr achieved (e.g. 18.00%) — use 0.00% for crashes
3. max_drawdown in percent, round to .2f - use 0.0 for crashes
4. status: keep, discard, or crash
5. short text description of what this experiment tried

Example:

```
commit	cagr	max_drawdown	status	description
a1b2c3d	16.25%  	  28.21%	keep	baseline
b2c3d4e	18.25%	      25.33%	keep	added additional EMA
c3d4e5f	14.25%	      20.56%	discard	remove RSI filtering
d4e5f6g	0.00%            0.0	crash	invalid trade entry logic
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autostratdev/mar5` or `autostratdev/mar5-cpu0`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `backtest.py` with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment: `uv run python -m strategy_dev.backtest > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "^cagr:\|^max_drawdown:\|^profit_factor:\|^sharpe:\|^win_rate:\|^number_of_trades:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the Python stack trace and attempt a fix. If you can't get things to work after more than a few attempts, give up.
7. Record the results in the tsv (NOTE: do not commit the results.tsv file, leave it untracked by git)
8. If cagr improved (higher), you "advance" the branch, keeping the git commit
9. If cagr is equal or worse, you git reset back to where you started
10. For marginal changes use `Volatility criterion` to decide.

You are a completely autonomous quant developer trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Crashes**: If a run crashes (OOM, or a bug, or etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the development loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — read papers, read famous quant blogs, re-read the in-scope files for new angles, try combining previous near-misses, try more radical architectural changes. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each development cycle takes you ~2 minutes then you can run approx 30/hour, for a total of about 240 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!