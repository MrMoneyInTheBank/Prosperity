import polars as pl

from processing.base_dataset import BaseDataset
from processing.constants import TRADES_SCHEMA, TRADES_DROP_COLS


class TradesDataset(BaseDataset):
    schema = TRADES_SCHEMA

    def for_product(self, product: str) -> "TradesDataProcessor":
        if product not in self.products():
            raise KeyError(f"{product} not found in {self.products()}")
        return TradesDataProcessor(
            self._raw_data.filter(pl.col("product") == product), product=product
        )


class TradesDataProcessor:
    def __init__(self, raw_data: pl.DataFrame, product: str) -> None:
        self._raw_data = raw_data
        self.product = product
