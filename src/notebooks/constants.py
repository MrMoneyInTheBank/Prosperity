import typing as t
from pathlib import Path

from src.utils.root import find_project_root

ROOT_DIR: t.Final[Path] = find_project_root(Path.cwd())
DATA_DIR: t.Final[Path] = ROOT_DIR / "data"

EMERALDS: t.Final[str] = "EMERALDS"

ORDERBOOK_LEVELS: t.Final[int] = 3

ROUND_0_DAY_M2_PRICES: t.Final[Path] = (
    DATA_DIR / "round-0/day_-2/prices_round_0_day_-1.csv"
)
ROUND_0_DAY_M2_TRADES: t.Final[Path] = (
    DATA_DIR / "round-0/day_-2/trades_round_0_day_-1.csv"
)
ROUND_0_DAY_M1_PRICES: t.Final[Path] = (
    DATA_DIR / "round-0/day_-1/prices_round_0_day_-1.csv"
)
ROUND_0_DAY_M1_TRADES: t.Final[Path] = (
    DATA_DIR / "round-0/day_-1/trades_round_0_day_-1.csv"
)
