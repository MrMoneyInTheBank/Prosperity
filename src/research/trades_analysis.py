import typing as t

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from numpy.typing import NDArray

from src.processing.trades import TradesDataProcessor
from src.research.results import Plot, Plots, TradesAnalysisResult


def plot_histogram(data: NDArray[np.int64], title: str, x_title: str) -> Plot:
    fig, ax = plt.subplots()
    ax.hist(data)
    ax.set_yscale("log")

    ax.set_xlabel(x_title)
    ax.set_ylabel("Frequency (log)")
    ax.set_title(title)

    plt.close(fig)

    return fig, ax


def analyse_time_intervals(trades_data: pl.DataFrame) -> pl.DataFrame:
    time_interval_stats: pl.DataFrame = trades_data.select(
        [
            pl.col("time_since_prev_trade").mean().alias("time_since_prev_mean"),
            pl.col("time_since_prev_trade").var().alias("time_since_prev_var"),
            pl.col("time_since_prev_trade").std().alias("time_since_prev_std"),
            pl.col("time_until_next_trade").mean().alias("time_until_next_mean"),
            pl.col("time_until_next_trade").var().alias("time_until_next_var"),
            pl.col("time_until_next_trade").std().alias("time_until_next_std"),
        ]
    )

    return time_interval_stats


def run_trades_analysis(
    raw_trades_data: TradesDataProcessor, orderbook_data: pl.DataFrame
) -> TradesAnalysisResult:
    trades_data: t.Final[pl.DataFrame] = (
        raw_trades_data.clean()
        .join_select_orderbook_data(orderbook_data)
        .add_time_features()
        .add_price_features()
        .add_buy_sell_heuristic()
        .build()
    )

    time_intervals_stats = analyse_time_intervals(trades_data)

    time_interval_prev_plot = plot_histogram(
        data=trades_data["time_since_prev_trade"].to_numpy(),
        title="Inter-arrival Time Distribution",
        x_title="Time since previous trade",
    )
    time_interval_next_plot = plot_histogram(
        data=trades_data["time_until_next_trade"].to_numpy(),
        title="Inter-arrival Time Distribution",
        x_title="Time until next trade",
    )

    plots = Plots(
        time_interval_until_plt=time_interval_prev_plot,
        time_interval_next_plt=time_interval_next_plot,
    )

    return TradesAnalysisResult(
        raw_trades_data=raw_trades_data,
        trades_data=trades_data,
        time_interval_stats=time_intervals_stats,
        plots=plots,
    )
