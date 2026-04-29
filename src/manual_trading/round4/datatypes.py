import math as m
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Mapping, Optional, Union


class Underlying(StrEnum):
    AC = "AETHER_CRYSTAL"


class OptionSide(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass(frozen=True)
class Option:
    strike_price: int
    underlying: Underlying = Underlying.AC
    TTE_weeks: Literal[2, 3] = 3

    def __str__(self) -> str:
        base = f"AC_{self.strike_price}"
        suffix = self._ticker_suffix()

        if self.TTE_weeks != 3:
            return f"{base}_{suffix}_{self.TTE_weeks}"
        return f"{base}_{suffix}"

    def _ticker_suffix(self) -> str:
        raise NotImplementedError()


@dataclass(frozen=True, kw_only=True)
class VanillaOption(Option):
    side: OptionSide

    def _ticker_suffix(self) -> str:
        return "C" if self.side == OptionSide.CALL else "P"


@dataclass(frozen=True)
class ChooserOption(Option):
    decision_time_weeks: int = 2

    def __post_init__(self):
        if not (0 < self.decision_time_weeks < self.TTE_weeks):
            raise ValueError("Choose decision time not in valid range")

    def _ticker_suffix(self) -> str:
        return "CO"


@dataclass(frozen=True, kw_only=True)
class BinaryPut(Option):
    payoff: int

    def __post_init__(self):
        if self.payoff <= 0:
            raise ValueError("Payoff must be positive")

    def _ticker_suffix(self) -> str:
        return "BP"


@dataclass(frozen=True, kw_only=True)
class KnockOutPut(Option):
    barrier_price: int

    def __post_init__(self):
        if self.barrier_price <= 0:
            raise ValueError("Barrier must be positive")

    def _ticker_suffix(self) -> str:
        return "KO"


Product = Union[Underlying, Option]


@dataclass(frozen=True)
class Bid:
    price: float
    quantity: int


@dataclass(frozen=True)
class Ask:
    price: float
    quantity: int


@dataclass(frozen=True)
class Quote:
    bid: Bid
    ask: Ask


@dataclass(frozen=True)
class Market:
    quotes: Mapping[Product, Quote]


@dataclass
class BlackScholesResult:
    option: VanillaOption
    fair_value: float
    buy_edge: float
    sell_edge: float
    delta: float
    gamma: float
    vega: float


@dataclass(frozen=True)
class SimResult:
    product: Product
    fair_value: float
    payoffs_std: Optional[float]
    buy_edge: float
    sell_edge: float


@dataclass
class Order:
    product: Product
    side: Bid | Ask

    def __str__(self) -> str:
        action: str = "BUY"
        if isinstance(self.side, Ask):
            action = "SELL"
        return f"{self.product}: {action} {self.side.quantity} @ {m.floor(self.side.price)}"
