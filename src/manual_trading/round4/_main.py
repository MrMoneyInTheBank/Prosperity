from typing import Final

import numpy.typing as npt
from rich.console import Console

from src.manual_trading.round4.brownian_motion import generate_price_paths
from src.manual_trading.round4.constants import (
    AC_VOL_ANNUAL,
    RAW_QUOTES,
)
from src.manual_trading.round4.datatypes import (
    BlackScholesResult,
    Market,
    SimResult,
    Underlying,
    VanillaOption,
)
from src.manual_trading.round4.market import build_market, get_midprice
from src.manual_trading.round4.orders import get_orders
from src.manual_trading.round4.printing import (
    print_black_scholes_result,
    print_market_state,
    print_orders_results,
    print_simulation_results,
)
from src.manual_trading.round4.results import (
    get_black_scholes_results,
    get_simulation_results,
)
from src.manual_trading.round4.utils import steps_for_weeks


def main() -> None:
    market: Final[Market] = build_market(RAW_QUOTES)

    AC_initial_price: Final[float] = get_midprice(market, Underlying.AC)
    price_paths: Final[npt.NDArray] = generate_price_paths(
        AC_initial_price,
        AC_VOL_ANNUAL,
        num_paths=100000,
        steps=steps_for_weeks(3),
    )

    simulation_results: Final[list[SimResult]] = get_simulation_results(
        price_paths, market
    )
    black_scholes_results: Final[list[BlackScholesResult]] = get_black_scholes_results(
        market,
        AC_initial_price,
        [p for p in market.quotes.keys() if isinstance(p, VanillaOption)],
    )
    orders, delta, gamma = get_orders(
        market, price_paths, simulation_results, black_scholes_results
    )
    console: Final[Console] = Console()

    print_market_state(console, market)
    print_simulation_results(console, simulation_results)
    print_black_scholes_result(console, black_scholes_results)
    print_orders_results(console, orders, delta, gamma)


if __name__ == "__main__":
    main()
