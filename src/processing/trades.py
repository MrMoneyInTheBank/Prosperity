import polars as pl

from src.config.constants import (
    Order,
    TRADES_DROP_COLS,
    TRADES_SCHEMA,
    TRADES_ORDERBOOK_JOIN_COLS,
    TRADES_ORDERBOOK_JOIN_RENAMES,
)
from src.processing.base_dataset import BaseDataset
from src.processing.base_processor import BaseProcessor


class TradesDataset(BaseDataset):
    schema = TRADES_SCHEMA
    product_key = "symbol"

    def for_product(self, product: str) -> "TradesDataProcessor":
        if product not in self.products():
            raise KeyError(f"{product} not found in {self.products()}")
        return TradesDataProcessor(
            self._raw_data.filter(pl.col("symbol") == product), product=product
        )


class TradesDataProcessor(BaseProcessor):
    def __init__(self, raw_data: pl.DataFrame, product: str) -> None:
        self._data = raw_data
        self.product = product
        self._orderbook_joined = False

    def clean(self) -> "TradesDataProcessor":
        self._data = self._data.drop(TRADES_DROP_COLS)
        return self

    def add_time_features(self) -> "TradesDataProcessor":
        self._data = self._data.with_columns(
            (pl.col("timestamp") - pl.col("timestamp").shift(1)).alias(
                "time_since_prev_trade"
            )
        ).with_columns(
            (pl.col("timestamp").shift(-1) - pl.col("timestamp")).alias(
                "time_until_next_trade"
            )
        )

        return self

    def join_select_orderbook_data(
        self, orderbook_data: pl.DataFrame
    ) -> "TradesDataProcessor":
        self._data = self._data.join(
            other=orderbook_data.select(TRADES_ORDERBOOK_JOIN_COLS).rename(
                TRADES_ORDERBOOK_JOIN_RENAMES
            ),
            on="timestamp",
            how="left",
        )
        self._orderbook_joined = True

        return self

    def add_price_features(self) -> "TradesDataProcessor":
        if not self._orderbook_joined:
            print("Join data from orderbook first to add price features.")
            return self

        self._data = self._data.with_columns(
            (pl.col("price") - pl.col("mid_price")).alias("mid_price_dev")
        )
        return self

    def add_buy_sell_heuristic(self) -> "TradesDataProcessor":
        if not self._orderbook_joined:
            print("Join data from orderbook first to add price features.")
            return self

        bid_dist = (pl.col("price") - pl.col("best_bid")).abs()
        ask_dist = (pl.col("price") - pl.col("best_ask")).abs()

        self._data = self._data.with_columns(
            pl.when(bid_dist < ask_dist)
            .then(pl.lit(Order.SELL_ORDER))
            .when(bid_dist > ask_dist)
            .then(pl.lit(Order.BUY_ORDER))
            .otherwise(pl.lit(Order.UNKNOWN))
            .alias("side_heur")
        )

        return self

    def build(self) -> pl.DataFrame:
        return self._data
