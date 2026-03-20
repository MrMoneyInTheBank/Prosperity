from enum import StrEnum
import typing as t
import collections.abc as c

import polars as pl
import polars.type_aliases as pt

AggFnType = c.Callable[[c.Iterable[pt.IntoExpr]], pl.Expr]
SchemaType = dict[str, type[pl.DataType]]

ORDERBOOK_SCHEMA: t.Final[SchemaType] = {
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

ORDERBOOK_DROP_COLS: t.Final[list[str]] = ["day", "product", "profit_and_loss"]

TRADES_SCHEMA: t.Final[SchemaType] = {
    "timestamp": pl.Int64,
    "buyer": pl.String,
    "seller": pl.String,
    "symbol": pl.String,
    "currency": pl.String,
    "price": pl.Float64,
    "quantity": pl.Int64,
}

TRADES_DROP_COLS: t.Final[list[str]] = ["buyer", "seller", "currency"]


class Side(StrEnum):
    BID = "bid"
    ASK = "ask"


class QuoteField(StrEnum):
    PRICE = "price"
    VOLUME = "volume"
