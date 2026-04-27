import math as m
from dataclasses import dataclass
from enum import StrEnum
from rich.table import Table
from rich.console import Console
from types import MappingProxyType
from typing import Final, Literal, Mapping, Optional, Union
from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as npt
from scipy.stats import norm

### CONSTANTS

TRADING_DAYS_PER_YEAR: Final[int] = 252
TRADING_DAYS_PER_WEEK: Final[int] = 5
STEPS_PER_DAY: Final[int] = 4
STEPS_PER_YEAR: Final[int] = STEPS_PER_DAY * TRADING_DAYS_PER_YEAR


AC_VOL_ANNUAL: Final[float] = 2.51

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

### BLACK SCHOLES


class BlackScholes(ABC):
    def __init__(self, sigma: float = AC_VOL_ANNUAL, r: float = 0):
        self.sigma = sigma
        self.r = r

    def _d1_d2(self, K: float, S: float, T: float) -> tuple[float, float]:
        sqrtT = m.sqrt(T)

        d1 = (m.log(S / K) + (self.r + 0.5 * self.sigma**2) * T) / (self.sigma * sqrtT)

        d2 = d1 - self.sigma * sqrtT

        return d1, d2

    def gamma(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return norm.pdf(d1) / (S * self.sigma * m.sqrt(T))

    def vega(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return S * norm.pdf(d1) * m.sqrt(T)

    @abstractmethod
    def price(self, K: float, S: float, T: float) -> float:
        raise NotImplementedError()


class BlackScholesCall(BlackScholes):
    def __init__(self, sigma: float = AC_VOL_ANNUAL, r: float = 0):
        super().__init__(sigma, r)

    def price(self, K: float, S: float, T: float) -> float:

        d1, d2 = self._d1_d2(K, S, T)

        return S * norm.cdf(d1) - K * m.exp(-self.r * T) * norm.cdf(d2)

    def delta(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return norm.cdf(d1)


class BlackScholesPut(BlackScholes):
    def __init__(self, sigma: float = AC_VOL_ANNUAL, r: float = 0):
        super().__init__(sigma, r)

    def price(self, K: float, S: float, T: float) -> float:

        d1, d2 = self._d1_d2(K, S, T)
        return K * m.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    def delta(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return -norm.cdf(d1)


@dataclass
class BlackSholesResults:
    option: VanillaOption
    fair_value: float
    delta: float
    gamma: float
    vega: float

### END OF BLACK SCHOLES

### SIMULATION


@dataclass(frozen=True)
class SimResults:
    product: Product
    payoffs_std: Optional[float]
    buy_edge: float
    sell_edge: float

    def __str__(self) -> str:
        if self.payoffs_std is None:
            return f"{self.product}: BUY_EDGE = {self.buy_edge:.4f}, SELL_EDGE = {self.sell_edge:.4f}"
        return f"{self.product}: BUY_EDGE = {self.buy_edge:.4f}, SELL_EDGE = {self.sell_edge:.4f}, PAYOFFS_STD: {self.payoffs_std:.4f}"


def generate_price_paths(
    initial_price: float,
    vol: float,
    num_paths: int,
    steps: int,
) -> npt.NDArray[np.float64]:
    dt = 1 / STEPS_PER_YEAR

    Z = np.random.normal(size=(num_paths, steps))

    log_returns = (-0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z

    log_price_paths = np.cumsum(log_returns, axis=1)

    price_paths = initial_price * np.exp(log_price_paths)

    initial_column = np.full((num_paths, 1), initial_price)
    price_paths = np.hstack([initial_column, price_paths])

    return price_paths


def get_underlying_sim_res(
    market: Market, underlying: Underlying, last_prices: npt.NDArray
):
    bid, ask = market.quotes[underlying].bid.price, market.quotes[underlying].ask.price

    fair_value: float = float(np.mean(last_prices))
    buy_edge: float = fair_value - ask
    sell_edge: float = bid - fair_value

    return SimResults(
        product=underlying, payoffs_std=None, buy_edge=buy_edge, sell_edge=sell_edge
    )


def get_vanilla_options_sim_res(
    market: Market, option: VanillaOption, last_prices: npt.NDArray
) -> SimResults:
    bid, ask = market.quotes[option].bid.price, market.quotes[option].ask.price

    payoffs: npt.NDArray = (
        np.maximum(last_prices - option.strike_price, 0)
        if option.side == OptionSide.CALL
        else np.maximum(option.strike_price - last_prices, 0)
    )

    payoffs_std: float = float(np.std(payoffs))
    fair_value: float = float(np.mean(payoffs))

    buy_edge: float = fair_value - ask
    sell_edge: float = bid - fair_value

    return SimResults(
        product=option, payoffs_std=payoffs_std, buy_edge=buy_edge, sell_edge=sell_edge
    )


def get_simulation_results(
    price_paths: npt.NDArray, market: Market
) -> list[SimResults]:
    two_week_steps = steps_for_weeks(2)

    last_prices: Final[npt.NDArray] = price_paths[:, -1]
    two_week_prices: Final[npt.NDArray] = price_paths[:, two_week_steps]

    results = []
    for product in market.quotes.keys():
        if isinstance(product, Underlying):
            results.append(get_underlying_sim_res(market, product, last_prices))
        elif isinstance(product, VanillaOption):
            if product.TTE_weeks == 2:
                results.append(
                    get_vanilla_options_sim_res(market, product, two_week_prices),
                )

            else:
                results.append(
                    get_vanilla_options_sim_res(market, product, last_prices),
                )

        else:
            continue

    return results


def print_simulation_results(results: list[SimResults]) -> None:
    table = Table(title="Simulation Results")
    table.add_column("Product", style="bold", justify="center")
    table.add_column("Buy Edge", justify="center")
    table.add_column("Sell Edge", justify="center")
    table.add_column("Payoffs std", justify="center")
    table.add_column("Buy Score", justify="center")
    table.add_column("Sell Score", justify="center")

    for res in results:
        table.add_row(
            str(res.product),
            f"{res.buy_edge:.4f}",
            f"{res.sell_edge:.4f}",
            f"{res.payoffs_std:.4f}" if res.payoffs_std is not None else "N/A",
            (
                f"{(res.buy_edge / res.payoffs_std):.4f}"
                if res.payoffs_std is not None
                else "N/A"
            ),
            (
                f"{(res.sell_edge / res.payoffs_std):.4f}"
                if res.payoffs_std is not None
                else "N/A"
            ),
        )

    Console().print(table)


### END OF SIMULATION

if __name__ == "__main__":
    market: Final[Market] = build_market(RAW_QUOTES)
    print_market_state(market)

    AC_initial_price: Final[float] = get_midprice(market, Underlying.AC)
    price_paths: Final[npt.NDArray] = generate_price_paths(
        AC_initial_price,
        AC_VOL_ANNUAL,
        num_paths=10000,
        steps=steps_for_weeks(3),
    )

    results = get_simulation_results(price_paths, market)
    print_simulation_results(results)
