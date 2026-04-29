from typing import Optional
import numpy.typing as npt

from src.manual_trading.round4.option_metrics import get_delta
from src.manual_trading.round4.utils import steps_for_weeks
from src.manual_trading.round4.datatypes import (
    Ask,
    Bid,
    BlackScholesResult,
    ChooserOption,
    BinaryPut,
    KnockOutPut,
    VanillaOption,
    Product,
    Market,
    SimResult,
    Underlying,
    Order,
)


def get_product_res(
    product: Product, sim_res: list[SimResult], bs_res: list[BlackScholesResult]
) -> tuple[Optional[SimResult], Optional[BlackScholesResult]]:
    sim = next((s for s in sim_res if s.product == product), None)
    bs = (
        next((b for b in bs_res if b.option == product), None)
        if isinstance(product, VanillaOption)
        else None
    )
    return sim, bs


def get_orders(
    market: Market,
    price_paths: npt.NDArray,
    sim_res: list[SimResult],
    bs_res: list[BlackScholesResult],
) -> tuple[list[Order], float, float]:
    orders = []

    scale: float = 100
    net_delta: float = 0
    net_gamma: float = 0

    for product, quote in market.quotes.items():
        if isinstance(product, Underlying):
            continue

        sim, bs = get_product_res(product, sim_res, bs_res)
        assert sim is not None
        assert sim.payoffs_std is not None

        if sim.buy_edge < 0 and sim.sell_edge < 0:
            continue

        buy = True if sim.buy_edge > 0 else False
        kelly = (
            max(abs(sim.buy_edge), abs(sim.sell_edge)) / sim.payoffs_std
        )  # Remove the **2
        kelly_fraction = min(kelly * scale, 1.0)
        available_qty = quote.ask.quantity if buy else quote.bid.quantity

        qty = max(1, int(kelly_fraction * available_qty))
        price = quote.bid.price if buy else quote.ask.price

        delta_contri = None

        if bs is not None:
            delta_contri = bs.delta
        elif isinstance(product, (ChooserOption, BinaryPut, KnockOutPut)):
            two_week_steps = steps_for_weeks(2)
            two_week_prices = price_paths[:, two_week_steps]
            last_prices = price_paths[:, -1]

            delta_contri = get_delta(product, price_paths, last_prices, two_week_prices)

        assert delta_contri is not None

        if buy:
            net_delta = net_delta + qty * delta_contri
            net_gamma = net_gamma + qty * (bs.gamma if bs else 0.0)

            orders.append(Order(product=product, side=Bid(price=price, quantity=qty)))
        else:
            net_delta = net_delta + qty * delta_contri
            net_gamma = net_gamma + qty * (bs.gamma if bs else 0.0)

            orders.append(Order(product=product, side=Ask(price=price, quantity=qty)))

    if abs(net_delta) > 0.5:
        underlying_quote = market.quotes[Underlying.AC]
        if net_delta > 0:
            orders.insert(
                0,
                Order(
                    Underlying.AC, Ask(underlying_quote.ask.price, int(abs(net_delta)))
                ),
            )
            net_delta -= int(abs(net_delta))
        else:
            orders.insert(
                0,
                Order(
                    Underlying.AC, Bid(underlying_quote.bid.price, int(abs(net_delta)))
                ),
            )

            net_delta += int(abs(net_delta))

    return orders, net_delta, net_gamma
