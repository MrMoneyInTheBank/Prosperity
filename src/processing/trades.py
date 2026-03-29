import polars as pl

from src.config.constants import TRADES_DROP_COLS, TRADES_SCHEMA
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

    def build(self) -> pl.DataFrame:
        return self._data
