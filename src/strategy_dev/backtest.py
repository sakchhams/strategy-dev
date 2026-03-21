from typing import Any, cast

import numpy as np
import pandas as pd
import talib

from strategy_dev.data import BookKeeper, TradeEntry, load_data

Float64Array = np.ndarray[tuple[Any, ...], np.dtype[np.float64]]


def _float64_array(series: pd.Series) -> Float64Array:
    return cast(Float64Array, np.asarray(series.to_numpy(dtype=np.float64), dtype=np.float64))


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    close = _float64_array(df["Close"])
    df["ema_89"] = talib.EMA(close, timeperiod=89)
    df["ema_233"] = talib.EMA(close, timeperiod=233)
    df["above_previous"] = df["Close"] > df["Close"].shift(1)
    return df.dropna()


def _generate_signal(row: pd.Series, position: TradeEntry | None) -> str:
    trend_gap = row["ema_233"] * 0.001  # 0.1% of the ema_233 value
    long_bias = (row["Close"] > row["ema_89"] + trend_gap) and (row["ema_233"] < row["ema_89"])
    short_bias = (row["Close"] < row["ema_89"] - trend_gap) and (row["ema_233"] > row["ema_89"])
    if position is None:
        if long_bias:
            return "long"
        if short_bias:
            return "short"
    elif position.is_long:
        stoploss = max(row["ema_89"], row["ema_233"])
        if row["Close"] < stoploss:
            return "exit"
    else:
        stoploss = min(row["ema_89"], row["ema_233"])
        if row["Close"] > stoploss:
            return "exit"
    return "hold"


def run_trades(d_f: pd.DataFrame, bookkeeper: BookKeeper) -> None:
    d_f = _build_features(d_f)
    for idx, row in d_f.iterrows():
        ts: pd.Timestamp = pd.to_datetime(idx)  # type: ignore
        signal = _generate_signal(row, bookkeeper.position)
        if signal == "long" or signal == "short":
            bookkeeper.open_trade(ts, row["Close"], signal == "long", 1)
        elif signal == "exit":
            bookkeeper.close_trade(ts, row["Close"])


def main() -> None:
    d_f = load_data("2h")
    bookkeeper = BookKeeper()
    run_trades(d_f, bookkeeper)
    bookkeeper.print_metrics()


if __name__ == "__main__":
    main()
