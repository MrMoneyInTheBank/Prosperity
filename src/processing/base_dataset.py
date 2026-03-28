import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

import polars as pl

from src.processing.base_processor import BaseProcessor


class BaseDataset(ABC):
    schema: t.ClassVar[dict[str, type[pl.DataType]]]
    product_key: t.ClassVar[str]

    def __init__(self, csv_path: Path) -> None:
        self.csv_path: Path = csv_path
        self._raw_data: pl.DataFrame = self.load_csv()
        self.validate_schema()

    def load_csv(self) -> pl.DataFrame:
        try:
            return pl.read_csv(source=self.csv_path, separator=";")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find csv file at given location: {self.csv_path}"
            )

    def validate_schema(self) -> None:
        cols: set[str] = set(self._raw_data.columns)
        expected_cols: set[str] = set(self.schema)

        missing_cols: set[str] = expected_cols - cols
        extra_cols: set[str] = cols - expected_cols

        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")
        if extra_cols:
            raise ValueError(f"Extra columns: {extra_cols}")

        for col, expected_dtype in self.schema.items():
            actual_dtype = self._raw_data.schema[col]

            if actual_dtype != expected_dtype:
                raise TypeError(
                    f"Column '{col}' has dtype {actual_dtype}, expected {expected_dtype}"
                )

    def products(self) -> list[str]:
        return self._raw_data.select(self.product_key).unique().to_series().to_list()

    @abstractmethod
    def for_product(self, product: str) -> BaseProcessor:
        pass
