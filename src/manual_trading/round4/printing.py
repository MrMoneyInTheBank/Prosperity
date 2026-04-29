from typing import Any, Callable, Iterable

from rich.console import Console
from rich.table import Table

from src.manual_trading.round4.datatypes import (
    Ask,
    BlackScholesResult,
    Market,
    Order,
    SimResult,
)


def print_table(
    console: Console,
    title: str,
    columns: list[tuple[str, dict]],
    rows: Iterable[Any],
    row_fn: Callable[[Any], list[str]],
) -> None:
    table = Table(title=title)

    # Add columns
    for col_name, col_kwargs in columns:
        table.add_column(col_name, **col_kwargs)

    # Add rows
    for row in rows:
        table.add_row(*row_fn(row))

    console.print(table)


def fmt_float(x: float, digits: int = 4) -> str:
    return f"{x:.{digits}f}"


def fmt_optional(x: float | None, digits: int = 4) -> str:
    return f"{x:.{digits}f}" if x is not None else "N/A"


def print_market_state(console: Console, market: Market) -> None:
    print_table(
        console,
        title="Market Snapshot",
        columns=[
            ("Bid Qty", {"justify": "center"}),
            ("Bid Price", {"justify": "center"}),
            ("Ticker", {"justify": "center", "style": "bold"}),
            ("Ask Price", {"justify": "center"}),
            ("Ask Qty", {"justify": "center"}),
        ],
        rows=market.quotes.items(),
        row_fn=lambda item: [
            str(item[1].bid.quantity),
            f"{item[1].bid.price:.3f}",
            str(item[0]),
            f"{item[1].ask.price:.3f}",
            str(item[1].ask.quantity),
        ],
    )


def print_black_scholes_result(
    console: Console, results: list[BlackScholesResult]
) -> None:
    print_table(
        console,
        title="Black Scholes Result",
        columns=[
            ("Product", {"justify": "center", "style": "bold"}),
            ("Fair Value", {"justify": "center"}),
            ("Buy Edge", {"justify": "center"}),
            ("Sell Edge", {"justify": "center"}),
            ("Delta", {"justify": "center"}),
            ("Gamma", {"justify": "center"}),
            ("Vega", {"justify": "center"}),
        ],
        rows=results,
        row_fn=lambda r: [
            str(r.option),
            fmt_float(r.fair_value),
            fmt_float(r.buy_edge),
            fmt_float(r.sell_edge),
            fmt_float(r.delta),
            fmt_float(r.gamma),
            fmt_float(r.vega),
        ],
    )


def print_simulation_results(console: Console, results: list[SimResult]) -> None:
    print_table(
        console,
        title="Simulation Results",
        columns=[
            ("Product", {"justify": "center", "style": "bold"}),
            ("Fair Value", {"justify": "center"}),
            ("Buy Edge", {"justify": "center"}),
            ("Sell Edge", {"justify": "center"}),
            ("Payoffs std", {"justify": "center"}),
            ("Buy Score", {"justify": "center"}),
            ("Sell Score", {"justify": "center"}),
        ],
        rows=results,
        row_fn=lambda r: [
            str(r.product),
            fmt_float(r.fair_value),
            fmt_float(r.buy_edge),
            fmt_float(r.sell_edge),
            fmt_optional(r.payoffs_std),
            (
                fmt_float(r.buy_edge / r.payoffs_std)
                if r.payoffs_std is not None
                else "N/A"
            ),
            (
                fmt_float(r.sell_edge / r.payoffs_std)
                if r.payoffs_std is not None
                else "N/A"
            ),
        ],
    )


def print_orders_results(
    console: Console,
    orders: list[Order],
    delta: float,
    gamma: float,
) -> None:
    print_table(
        console,
        title="Orders",
        columns=[
            ("Product", {"justify": "center"}),
            ("Side", {"justify": "center"}),
            ("Price", {"justify": "center", "style": "bold"}),
            ("Qty", {"justify": "center"}),
        ],
        rows=orders,
        row_fn=lambda o: [
            str(o.product),
            "SELL" if isinstance(o.side, Ask) else "BUY",
            str(o.side.price),
            str(o.side.quantity),
        ],
    )

    print_table(
        console,
        title="Portfolio Greeks",
        columns=[
            ("Metric", {"justify": "center"}),
            ("Value", {"justify": "center"}),
        ],
        rows=[
            ("Net Delta", fmt_float(delta, 2)),
            ("Net Gamma", fmt_float(gamma, 6)),
        ],
        row_fn=lambda r: list(r),
    )
