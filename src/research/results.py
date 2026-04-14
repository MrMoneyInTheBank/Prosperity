from dataclasses import dataclass

import polars as pl

from src.processing.orderbook import OrderBookDataProcessor
from src.processing.trades import TradesDataProcessor
from src.research.plots import Plots


@dataclass(frozen=True)
class OrderbookAnalysisResult:
    raw_orderbook_data: OrderBookDataProcessor
    orderbook_data: pl.DataFrame
    orderbook_features_data: pl.DataFrame
    orderbook_stats: pl.DataFrame
    orderbook_corrs: pl.DataFrame


@dataclass(frozen=True)
class TradesAnalysisResult:
    raw_trades_data: TradesDataProcessor
    trades_data: pl.DataFrame
    time_interval_stats: pl.DataFrame
    quantities_stats: pl.DataFrame
    order_side_stats: pl.DataFrame
    trade_price_streaks_stats: pl.DataFrame


@dataclass(frozen=True)
class AnalysisResult:
    orderbook_analysis_result: OrderbookAnalysisResult
    trades_analysis_result: TradesAnalysisResult
    plots: Plots
