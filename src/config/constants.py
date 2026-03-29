import collections.abc as c
import typing as t
from enum import StrEnum
from pathlib import Path

import polars as pl
import polars.type_aliases as pt

from src.utils import find_project_root

### TYPES

AggFnType = c.Callable[[c.Iterable[pt.IntoExpr]], pl.Expr]
SchemaType = dict[str, type[pl.DataType]]

### CONSTANTS

## Paths

# Directories
ROOT_DIR: t.Final[Path] = find_project_root(Path(__file__).resolve())
DATA_DIR: t.Final[Path] = ROOT_DIR / "data"
SRC_DIR: t.Final[Path] = ROOT_DIR / "src"
TEMPLATES_DIR: t.Final[Path] = SRC_DIR / "templates"
TRADERS_DIR: t.Final[Path] = ROOT_DIR / "src" / "traders"
PRODUCT_TRADERS_DIR: t.Final[Path] = TRADERS_DIR / "product_traders"
TRADERS_HISTORY_DIR: t.Final[Path] = TRADERS_DIR / "history"


# Files
TRADER_HEADER_FILE: t.Final[Path] = TEMPLATES_DIR / "trader_header.txt"
TRADER_FOOTER_FILE: t.Final[Path] = TEMPLATES_DIR / "trader_footer.txt"
TRADER_FILE: t.Final[Path] = TRADERS_DIR / "trader.py"


class Product(StrEnum):
    EMERALDS = "EMERALDS"
    TOMATOES = "TOMATOES"


# Position limits

POS_LIMITS: t.Final[dict[Product, int]] = {Product.EMERALDS: 80, Product.TOMATOES: 80}


# Orderbook
class Side(StrEnum):
    BID = "bid"
    ASK = "ask"


class QuoteField(StrEnum):
    PRICE = "price"
    VOLUME = "volume"


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
ORDERBOOK_FEATURES: t.Final[list[str]] = [
    "mid_price",
    "spread",
    "imbalance",
    "log_returns",
    "future_log_returns",
    "microprice",
    "microprice_dev",
    "depth",
]

ORDERBOOK_LEVELS: t.Final[int] = 3

# Trades
TRADES_SCHEMA: t.Final[SchemaType] = {
    "timestamp": pl.Int64,
    "buyer": pl.String,
    "seller": pl.String,
    "symbol": pl.String,
    "currency": pl.String,
    "price": pl.Float64,
    "quantity": pl.Int64,
}

TRADES_DROP_COLS: t.Final[list[str]] = ["buyer", "seller", "symbol", "currency"]
