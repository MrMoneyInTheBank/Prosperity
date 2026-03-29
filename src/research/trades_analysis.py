import typing as t

import polars as pl

from src.processing.trades import TradesDataProcessor
from src.research.results import TradesAnalysisResult


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

    return TradesAnalysisResult(
        raw_trades_data=raw_trades_data, trades_data=trades_data
    )
