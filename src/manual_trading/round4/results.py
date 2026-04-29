from typing import Final, Optional

import numpy as np
import numpy.typing as npt

from src.manual_trading.round4.black_scholes import BlackScholesCall, BlackScholesPut
from src.manual_trading.round4.constants import (
    TRADING_DAYS_PER_WEEK,
    TRADING_DAYS_PER_YEAR,
)
from src.manual_trading.round4.datatypes import (
    BlackScholesResult,
    Market,
    Option,
    OptionSide,
    SimResult,
    Underlying,
    VanillaOption,
)
from src.manual_trading.round4.option_metrics import get_payoffs
from src.manual_trading.round4.utils import steps_for_weeks


def get_black_scholes_results(
    market: Market, underlying_midprice: float, options: list[VanillaOption]
) -> list[BlackScholesResult]:

    res: list[BlackScholesResult] = []
    BS_CALL = BlackScholesCall()
    BS_PUT = BlackScholesPut()

    for opt in options:
        bid, ask = market.quotes[opt].bid.price, market.quotes[opt].ask.price

        fair_value: Optional[float] = None
        delta: Optional[float] = None
        T: float = (opt.TTE_weeks * TRADING_DAYS_PER_WEEK) / TRADING_DAYS_PER_YEAR
        gamma: float = BS_CALL.gamma(opt.strike_price, underlying_midprice, T)
        vega: float = BS_CALL.vega(opt.strike_price, underlying_midprice, T)

        if opt.side == OptionSide.CALL:
            fair_value = BS_CALL.price(opt.strike_price, underlying_midprice, T)
            delta = BS_CALL.delta(opt.strike_price, underlying_midprice, T)
        else:
            fair_value = BS_PUT.price(opt.strike_price, underlying_midprice, T)
            delta = BS_PUT.delta(opt.strike_price, underlying_midprice, T)

        buy_edge: float = fair_value - ask
        sell_edge: float = bid - fair_value
        res.append(
            BlackScholesResult(opt, fair_value, buy_edge, sell_edge, delta, gamma, vega)
        )

    return res


def get_underlying_sim_res(
    market: Market, underlying: Underlying, last_prices: npt.NDArray
):
    bid, ask = market.quotes[underlying].bid.price, market.quotes[underlying].ask.price

    fair_value: float = float(np.mean(last_prices))
    buy_edge: float = fair_value - ask
    sell_edge: float = bid - fair_value

    return SimResult(
        product=underlying,
        fair_value=fair_value,
        payoffs_std=None,
        buy_edge=buy_edge,
        sell_edge=sell_edge,
    )


def get_options_sim_res(
    market: Market,
    option: Option,
    price_paths: npt.NDArray,
    last_prices: npt.NDArray,
    two_week_prices: npt.NDArray,
) -> SimResult:

    bid, ask = market.quotes[option].bid.price, market.quotes[option].ask.price

    payoffs: npt.NDArray = get_payoffs(
        option, price_paths, last_prices, two_week_prices
    )

    payoffs_std: float = float(np.std(payoffs))
    fair_value: float = float(np.mean(payoffs))

    buy_edge: float = fair_value - ask
    sell_edge: float = bid - fair_value

    return SimResult(
        product=option,
        fair_value=fair_value,
        payoffs_std=payoffs_std,
        buy_edge=buy_edge,
        sell_edge=sell_edge,
    )


def get_simulation_results(price_paths: npt.NDArray, market: Market) -> list[SimResult]:
    two_week_steps = steps_for_weeks(2)

    last_prices: Final[npt.NDArray] = price_paths[:, -1]
    two_week_prices: Final[npt.NDArray] = price_paths[:, two_week_steps]

    results = []
    for product in market.quotes.keys():
        if isinstance(product, Underlying):
            results.append(get_underlying_sim_res(market, product, last_prices))
        elif isinstance(product, Option):
            results.append(
                get_options_sim_res(
                    market, product, price_paths, last_prices, two_week_prices
                )
            )

    return results
