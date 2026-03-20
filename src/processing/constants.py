from enum import StrEnum
import typing as t

import polars as pl

ORDERBOOK_SCHEMA: t.Final[t.Dict[str, type[pl.DataType]]] = {
    "day": pl.Int64,
    "timestamp": pl.Int64,
    "product": pl.String,
    "bid_price_1": pl.Int64,
    "bid_volume_1": pl.Int64,
    "bid_price_2": pl.Int64,
    "bid_volume_2": pl.Int64,
    "bid_price_3": pl.Int64,
    "bid_volume_3": pl.Int64,
    "ask_price_1": pl.Int64,
    "ask_volume_1": pl.Int64,
    "ask_price_2": pl.Int64,
    "ask_volume_2": pl.Int64,
    "ask_price_3": pl.Int64,
    "ask_volume_3": pl.Int64,
    "mid_price": pl.Float64,
    "profit_and_loss": pl.Float64,
}

ORDERBOOK_DROP_COLS: t.Final[t.List[str]] = ["day", "product", "profit_and_loss"]


class Side(StrEnum):
    BID = "bid"
    ASK = "ask"


class QuoteField(StrEnum):
    PRICE = "price"
    VOLUME = "volume"
