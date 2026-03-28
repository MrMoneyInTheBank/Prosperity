from pathlib import Path
from dataclasses import dataclass

from src.notebooks.constants import DATA_DIR

@dataclass(frozen=True)
class DatasetSpec:
    round_number: int
    day: int

    def __post_init__(self):
        prices_path = self.prices()
        trades_path = self.trades()

        if not prices_path.exists():
            raise FileNotFoundError(f"Prices file not found: {prices_path}")

        if not trades_path.exists():
            raise FileNotFoundError(f"Trades file not found: {trades_path}")

    def prices(self) -> Path:
        return DATA_DIR / f"round-{self.round_number}/day_{self.day}/prices_round_{self.round_number}_day_{self.day}.csv"

    def trades(self) -> Path:
        return DATA_DIR / f"round-{self.round_number}/day_{self.day}/trades_round_{self.round_number}_day_{self.day}.csv"