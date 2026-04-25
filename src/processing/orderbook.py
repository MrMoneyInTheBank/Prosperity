import math
import typing as t

import polars as pl

from src.config.constants import (
    ORDERBOOK_DROP_COLS,
    ORDERBOOK_SCHEMA,
    AggFnType,
    QuoteField,
    Side,
)
from src.processing.base_dataset import BaseDataset
from src.processing.base_processor import BaseProcessor


class OrderBookDataset(BaseDataset):
    schema = ORDERBOOK_SCHEMA
    product_key = "product"

    def for_product(self, product: str | t.Literal["VEV_"]) -> "OrderBookDataProcessor":
        if product == "VEV_":
            return OrderBookDataProcessor(
                self._raw_data.filter(pl.col("product").str.starts_with("VEV_")),
                product="VELVETFRUIT_OPTIONS",
            )
        if product not in self.products():
            raise KeyError(f"{product} not found in {self.products()}")
        return OrderBookDataProcessor(
            self._raw_data.filter(pl.col("product") == product), product=product
        )


def quote_horizontal(
    agg_fn: AggFnType, side: Side, field: QuoteField, level: int = 3
) -> pl.Expr:
    side_str = side.value
    field_str = field.value

    return agg_fn([pl.col(f"{side_str}_{field_str}_{i}") for i in range(1, level + 1)])


class OrderBookDataProcessor(BaseProcessor):
    def __init__(self, raw_data: pl.DataFrame, product: str) -> None:
        self._data = raw_data
        self.product = product

    def clean(self) -> "OrderBookDataProcessor":
        self._data = self._data.drop(ORDERBOOK_DROP_COLS)
        self._data = self._data.filter(
            (pl.col("mid_price").is_not_null()) & (pl.col("mid_price") != 0)
        )
        return self

    def add_microstructure_features(self) -> "OrderBookDataProcessor":
        bid_vol = quote_horizontal(pl.sum_horizontal, Side.BID, QuoteField.VOLUME)
        ask_vol = quote_horizontal(pl.sum_horizontal, Side.ASK, QuoteField.VOLUME)

        self._data = self._data.with_columns(
            [
                (pl.col("ask_price_1") - pl.col("bid_price_1")).alias("spread"),
                ((bid_vol - ask_vol) / (bid_vol + ask_vol)).alias("imbalance"),
                (pl.col("mid_price") - pl.col("mid_price").mean()).alias(
                    "midprice_dev"
                ),
            ]
        )

        return self

    def add_price_features(self) -> "OrderBookDataProcessor":
        self._data = (
            self._data.with_columns(
                (pl.col("mid_price") / pl.col("mid_price").shift(1))
                .log(math.e)
                .alias("log_returns")
            )
            .with_columns(pl.col("log_returns").shift(-1).alias("future_log_returns"))
            .with_columns(
                (
                    (
                        (pl.col("ask_price_1") * pl.col("bid_volume_1"))
                        + (pl.col("bid_price_1") * pl.col("ask_volume_1"))
                    )
                    / (pl.col("bid_volume_1") + pl.col("ask_volume_1"))
                ).alias("microprice")
            )
            .with_columns(
                (pl.col("microprice") - pl.col("mid_price")).alias("microprice_dev")
            )
        )
        return self

    def add_depth_features(self) -> "OrderBookDataProcessor":
        self._data = self._data.with_columns(
            (pl.col("bid_volume_1") + pl.col("ask_volume_1")).alias("depth")
        )
        return self

    def build(self) -> pl.DataFrame:
        return self._data
