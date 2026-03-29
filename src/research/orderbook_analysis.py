import typing as t

import polars as pl

from src.config.constants import ORDERBOOK_FEATURES
from src.processing.orderbook import OrderBookDataProcessor
from src.research.results import OrderbookAnalysisResult


def run_orderbook_analysis(
    raw_orderbook_data: OrderBookDataProcessor,
) -> OrderbookAnalysisResult:
    orderbook_data: t.Final[pl.DataFrame] = (
        raw_orderbook_data.clean()
        .add_microstructure_features()
        .add_price_features()
        .add_depth_features()
        .build()
    )

    orderbook_features_data: t.Final[pl.DataFrame] = orderbook_data.select(
        ["timestamp", *ORDERBOOK_FEATURES]
    )

    orderbook_stats: t.Final[pl.DataFrame] = orderbook_features_data.select(
        [
            pl.col("mid_price").mean().alias("mid_mean"),
            pl.col("mid_price").var().alias("mid_var"),
            pl.col("mid_price").std().alias("mid_std"),
            pl.col("microprice").mean().alias("micro_mean"),
            pl.col("microprice").var().alias("micro_var"),
            pl.col("microprice").std().alias("micro_std"),
            pl.col("log_returns").mean().alias("ret_mean"),
            pl.col("log_returns").var().alias("ret_var"),
            pl.col("log_returns").std().alias("ret_std"),
        ]
    )

    orderbook_corrs: t.Final[pl.DataFrame] = orderbook_features_data.select(
        [
            pl.corr("imbalance", "future_log_returns").alias("imb_corr"),
            pl.corr("microprice_dev", "future_log_returns").alias("micro_corr"),
        ]
    )

    return OrderbookAnalysisResult(
        raw_orderbook_data=raw_orderbook_data,
        orderbook_data=orderbook_data,
        orderbook_features_data=orderbook_features_data,
        orderbook_stats=orderbook_stats,
        orderbook_corrs=orderbook_corrs,
    )
