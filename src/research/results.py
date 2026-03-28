from dataclasses import dataclass

import polars as pl

from src.processing.orderbook import OrderBookDataProcessor


@dataclass(frozen=True)
class AnalysisResult:
    raw_orderbook_data: OrderBookDataProcessor
    orderbook_data: pl.DataFrame
    orderbook_features_data: pl.DataFrame
    orderbook_stats: pl.DataFrame
    orderbook_corrs: pl.DataFrame
