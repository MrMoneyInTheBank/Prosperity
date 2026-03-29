import typing as t

import polars as pl

from src.config.constants import Product
from src.processing.dataset_spec import DatasetSpec
from src.processing.orderbook import OrderBookDataProcessor, OrderBookDataset
from src.processing.trades import TradesDataProcessor, TradesDataset
from src.research.orderbook_analysis import run_orderbook_analysis
from src.research.trades_analysis import run_trades_analysis
from src.research.results import (
    AnalysisResult,
    OrderbookAnalysisResult,
    TradesAnalysisResult,
)


def run_analysis(round: int, day: int, product: str) -> AnalysisResult:
    if product not in Product:
        raise KeyError(f"Product {product} not found in {Product._member_names_}")

    dataset: t.Final[DatasetSpec] = DatasetSpec(round_number=round, day=day)

    raw_orderbook_data: t.Final[OrderBookDataProcessor] = OrderBookDataset(
        dataset.prices()
    ).for_product(product)
    raw_trades_data: t.Final[TradesDataProcessor] = TradesDataset(
        dataset.trades()
    ).for_product(product)

    orderbook_analysis: OrderbookAnalysisResult = run_orderbook_analysis(
        raw_orderbook_data
    )
    trades_analysis: TradesAnalysisResult = run_trades_analysis(
        raw_trades_data, orderbook_data=orderbook_analysis.orderbook_data
    )
    return AnalysisResult(orderbook_analysis, trades_analysis)
