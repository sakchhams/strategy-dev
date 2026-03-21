import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

_valid_timeframes = ["1min", "5min", "15min", "30min", "1h", "2h", "4h", "1d"]
_SYMBOL = "NIFTY"
_CAPITAL = 250_000
_LOT_SIZE = 75


def load_data(timeframe: str) -> pd.DataFrame:
    """Load historical data for the specified timeframe."""
    if timeframe not in _valid_timeframes:
        raise ValueError(
            f"Invalid timeframe: {timeframe}. \
                         Valid timeframes are: {_valid_timeframes}"
        )
    file_path = f"data/{_SYMBOL}.pq"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    df = pd.read_parquet(file_path)
    # check if columns Open, High, Low, Close are present and index is datetime
    required_columns = {"Open", "High", "Low", "Close"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Data file must contain columns: {required_columns}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Data file index must be a DatetimeIndex")
    # resample df to timeframe candles
    df = df.resample(timeframe).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"})
    return df.dropna(subset=["Open", "High", "Low", "Close"])


@dataclass
class Trade:
    """Represents a completed trade with entry and exit details."""

    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    is_long: bool
    quantity: float

    def pnl(self) -> float:
        """Calculate the profit and loss for the trade."""
        if self.is_long:
            gross_pnl = (self.exit_price - self.entry_price) * self.quantity
            charges = _calculate_charges(self.entry_price, self.exit_price, self.quantity)
        else:
            gross_pnl = (self.entry_price - self.exit_price) * self.quantity
            charges = _calculate_charges(self.exit_price, self.entry_price, self.quantity)
        return gross_pnl - charges


@dataclass
class TradeEntry:
    """Represents an open position on the book."""

    time: pd.Timestamp
    price: float
    is_long: bool
    quantity: float


class BookKeeper:
    """Manages the current position and keeps a record of all completed trades."""

    def __init__(self) -> None:
        self.trades: list[Trade] = []
        self.position: TradeEntry | None = None
        self.lot_size = _LOT_SIZE

    def open_trade(self, time: pd.Timestamp, price: float, is_long: bool, quantity: float) -> None:
        """Open a new position on the book. \
            `quantity` is a fraction of the lot size to trade between 0 and 1."""
        if self.position is not None:
            raise ValueError(
                "Already have an open position.\
                              Close it before opening a new one."
            )
        if quantity < 0 or quantity > 1:
            raise ValueError(
                "Quantity must be in range (0,1],\
                      representing the fraction of the lot size to trade."
            )
        self.position = TradeEntry(time, price, is_long, quantity)

    def close_trade(self, exit_time: pd.Timestamp, exit_price: float) -> None:
        """Close the currently open position on the book."""
        if self.position is None:
            raise ValueError("No open position to close")
        trade = Trade(
            entry_time=self.position.time,
            exit_time=exit_time,
            entry_price=self.position.price,
            exit_price=exit_price,
            is_long=self.position.is_long,
            quantity=self.position.quantity * self.lot_size,
        )
        self.trades.append(trade)
        self.position = None

    def print_metrics(self) -> None:
        """Calculate and print performance metrics for the completed trades."""
        capital = _CAPITAL
        # get exit time and pnl for each trade and create a pandas dataframe
        data = [(trade.exit_time, trade.pnl()) for trade in self.trades]
        df = pd.DataFrame(data, columns=["exit_time", "pnl"])
        df["portfolio"] = capital + df["pnl"].cumsum()
        df["drawdown_pct"] = (df["portfolio"] / df["portfolio"].cummax() - 1) * 100
        sharpe_ratio = df["pnl"].mean() / df["pnl"].std() * np.sqrt(252)
        # calculate expectancy.
        # (average_win * win_rate) - (average_loss * loss_rate)
        expectancy = (df[df["pnl"] > 0]["pnl"].mean() * (df["pnl"] > 0).mean()) - (
            df[df["pnl"] < 0]["pnl"].mean() * (df["pnl"] < 0).mean()
        )
        # calculate CAGR
        years = (df["exit_time"].iloc[-1] - df["exit_time"].iloc[0]).days / 365
        cagr = (df["portfolio"].iloc[-1] / capital) ** (1 / years) - 1
        # absolute returns
        absolute_return = (df["portfolio"].iloc[-1] - capital) / capital
        # max drawdown
        max_drawdown = df["drawdown_pct"].min()
        # number of trades, win rate, loss rate, average win, average loss
        num_trades = len(self.trades)
        win_rate = (df["pnl"] > 0).mean()
        loss_rate = (df["pnl"] < 0).mean()
        average_win = df[df["pnl"] > 0]["pnl"].mean()
        average_loss = df[df["pnl"] < 0]["pnl"].mean()
        profit_factor = df[df["pnl"] > 0]["pnl"].sum() / -df[df["pnl"] < 0]["pnl"].sum()
        print(f"sharpe: {sharpe_ratio:.2f}")
        print(f"expectancy: {expectancy:.2f}")
        print(f"cagr: {cagr:.2%}")
        print(f"absolute_return: {absolute_return:.2%}")
        print(f"max_drawdown: {max_drawdown:.2f}%")
        print(f"number_of_trades: {num_trades}")
        print(f"win_rate: {win_rate:.2%}")
        print(f"loss_rate: {loss_rate:.2%}")
        print(f"average_win: {average_win:.2f}")
        print(f"average_loss: {average_loss:.2f}")
        print(f"profit_factor: {profit_factor:.2f}")


def _calculate_charges(buy: float, sell: float, quantity: float) -> float:
    charges: dict[str, float] = {}
    charges["stt"] = 0.0001 * sell * quantity
    charges["nse_fee"] = (buy + sell) * 0.00002 * quantity
    charges["brokerage"] = 40
    charges["gst"] = (charges["brokerage"] + charges["nse_fee"]) * 0.18
    charges["stamp_duty"] = 0.0002 * buy * quantity
    all_charges: list[float] = list(charges.values())
    return sum(all_charges)
