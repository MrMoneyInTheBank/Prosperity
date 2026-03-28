import typing as t
from pathlib import Path

from src.utils.root import find_project_root

ROOT_DIR: t.Final[Path] = find_project_root(Path(__file__).resolve())
DATA_DIR: t.Final[Path] = ROOT_DIR / "data"

EMERALDS: t.Final[str] = "EMERALDS"
TOMATOES: t.Final[str] = "TOMATOES"

ORDERBOOK_LEVELS: t.Final[int] = 3
