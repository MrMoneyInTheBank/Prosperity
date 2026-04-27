from dataclasses import dataclass
from enum import StrEnum
from rich.table import Table
from rich.console import Console
from types import MappingProxyType
from typing import Final, Literal, Mapping, Optional, Union

import numpy as np
import numpy.typing as npt

### CONSTANTS

TRADING_DAYS_PER_YEAR: Final[int] = 252
TRADING_DAYS_PER_WEEK: Final[int] = 5
STEPS_PER_DAY: Final[int] = 4
STEPS_PER_YEAR: Final[int] = STEPS_PER_DAY * TRADING_DAYS_PER_YEAR
STEPS_PER_THREE_WEEKS: Final[int] = STEPS_PER_DAY * TRADING_DAYS_PER_WEEK * 3


AC_VARIANCE_ANNUAL: Final[float] = 2.51
AC_VARIANCE_PER_STEP: Final[float] = AC_VARIANCE_ANNUAL * np.sqrt(1 / STEPS_PER_YEAR)

### END OF CONSTANTS

### UTILITY FUNCTIONS


def weeks_to_years(weeks: float) -> float:
    return (weeks * 5) / TRADING_DAYS_PER_YEAR


def steps_for_weeks(weeks: float) -> int:
    return int(round(weeks * 5 * STEPS_PER_DAY))


### END OF UTILITY FUNCTIONS

### PRODUCTS

# There is one underlying product AETHER_CRYSTAL and several options contracts on it.
# Types of options
## - Vanilla options: Vanilla call and put options with a specified strike price and TTE in weeks
## - Choose option: Chooser option which remains ambiguous until two weeks and decays into either a
##                  vanilla call or a vanilla put depending on which would be in the money in reference
##                  to the strike price
## - Binary put option: Vanilla put option with a specified strike price and TTE in weeks but with the
##                      augmentation that payoff is a specified amount if the option expires in the money
## - Knockout put option: Vanilla put option with a specified strike price, TTE in weeks, and a barrier price
##                        (35 currency units). Should the underlying price ever fall below the barrier price
##                        the option expires worthless. If it doesn't, then acts like a vanilla put option

# How to interprete a ticker
## Underlying: <UNDERLYING_SYMBOL>
## OPTIONS: <UNDERLYING_SYMBOL>_<STRIKE_PRICE>_<TTE>_<TYPE>

## Note that default TTE is 3 weeks. Therefore only options with an expiry of 2 weeks are marked as having so.
## Additionally, the option type is only specified if the option is not a vanilla option. For the knockout put
## option, the barrier price is 35 currency units.

## Legend
### AC: underlying
### C: call option
### P: call option
### CO: chooser option
### BP: binary put option
### KO: knockout put option


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

AC_50_C = VanillaOption(strike_price=50, side=OptionSide.CALL)
AC_50_C_2 = VanillaOption(strike_price=50, side=OptionSide.CALL, TTE_weeks=2)
AC_60_C = VanillaOption(strike_price=60, side=OptionSide.CALL)
AC_35_P = VanillaOption(strike_price=35, side=OptionSide.PUT)
AC_40_P = VanillaOption(strike_price=40, side=OptionSide.PUT)
AC_45_P = VanillaOption(strike_price=45, side=OptionSide.PUT)
AC_50_P = VanillaOption(strike_price=50, side=OptionSide.PUT)
AC_50_P_2 = VanillaOption(strike_price=50, side=OptionSide.PUT, TTE_weeks=2)
AC_50_CO = ChooserOption(strike_price=50, decision_time_weeks=2)
AC_40_BP = BinaryPut(strike_price=40, payoff=10)
AC_45_KO = KnockOutPut(strike_price=45, barrier_price=35)

### END OF PRODUCTS


### MARKET


@dataclass
class Bid:
    price: float
    quantity: int


@dataclass
class Ask:
    price: float
    quantity: int


@dataclass
class Quote:
    bid: Bid
    ask: Ask


@dataclass(frozen=True)
class Market:
    quotes: Mapping[Product, Quote]


def build_market(raw_quotes: dict[Product, dict[str, list]]) -> Market:
    return Market(
        quotes=MappingProxyType(
            {
                product: Quote(bid=Bid(*quote["bid"]), ask=Ask(*quote["ask"]))
                for product, quote in raw_quotes.items()
            }
        )
    )


def print_market_state(market: Market) -> None:
    table = Table(title="Market Snapshot")

    table.add_column("Bid Qty", justify="center")
    table.add_column("Bid Price", justify="center")
    table.add_column("Ticker", style="bold", justify="center")
    table.add_column("Ask Price", justify="center")
    table.add_column("Ask Qty", justify="center")

    for p, q in market.quotes.items():
        table.add_row(
            str(q.bid.quantity),
            f"{q.bid.price:.3f}",
            str(p),
            f"{q.ask.price:.3f}",
            str(q.ask.quantity),
        )

    Console().print(table)


RAW_QUOTES: dict[Product, dict[str, list]] = {
    Underlying.AC: {"bid": [49.975, 200], "ask": [50.025, 200]},
    AC_50_C: {"bid": [12, 50], "ask": [12.05, 50]},
    AC_50_C_2: {"bid": [9.7, 50], "ask": [9.75, 50]},
    AC_60_C: {"bid": [8.8, 50], "ask": [8.85, 50]},
    AC_35_P: {"bid": [4.33, 50], "ask": [4.35, 50]},
    AC_40_P: {"bid": [6.5, 50], "ask": [6.55, 50]},
    AC_45_P: {"bid": [9.05, 50], "ask": [9.1, 50]},
    AC_50_P: {"bid": [12, 50], "ask": [12.05, 50]},
    AC_50_P_2: {"bid": [9.7, 50], "ask": [9.75, 50]},
    AC_50_CO: {"bid": [22.2, 50], "ask": [22.3, 50]},
    AC_40_BP: {"bid": [5, 50], "ask": [5.1, 50]},
    AC_45_KO: {"bid": [0.15, 500], "ask": [0.175, 500]},
}


def midprice(quote: Quote) -> float:
    return 0.5 * (quote.bid.price + quote.ask.price)


def get_midprice(market: Market, product: Product) -> float:
    return midprice(market.quotes[product])


### END OF MARKET


if __name__ == "__main__":
    market = build_market(RAW_QUOTES)
    print_market_state(market)
