from dataclasses import dataclass, fields

import matplotlib.pyplot as plt
import polars as pl

from src.processing.orderbook import OrderBookDataProcessor
from src.processing.trades import TradesDataProcessor


type Plot = tuple[plt.Figure, plt.Axes]


@dataclass(frozen=True)
class OrderbookAnalysisResult:
    raw_orderbook_data: OrderBookDataProcessor
    orderbook_data: pl.DataFrame
    orderbook_features_data: pl.DataFrame
    orderbook_stats: pl.DataFrame
    orderbook_corrs: pl.DataFrame


@dataclass(frozen=True)
class Plots:
    time_interval_until_plt: Plot
    time_interval_next_plt: Plot


def display_plots(plots: Plots) -> None:
    from IPython.display import display

    for field in fields(plots):
        plot = getattr(plots, field.name)
        display(plot[0])


@dataclass(frozen=True)
class TradesAnalysisResult:
    raw_trades_data: TradesDataProcessor
    trades_data: pl.DataFrame  # flesh this out later
    time_interval_stats: pl.DataFrame
    plots: Plots


@dataclass(frozen=True)
class AnalysisResult:
    orderbook_analysis_result: OrderbookAnalysisResult
    trades_analysis_result: TradesAnalysisResult
