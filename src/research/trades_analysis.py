import typing as t

import polars as pl

from src.config.constants import Order
from src.processing.trades import TradesDataProcessor
from src.research.plots import Plot, TradesPlots, plot_histogram
from src.research.results import TradesAnalysisResult


def analyse_time_intervals(time_interval_data: pl.DataFrame) -> pl.DataFrame:
    time_interval_stats: t.Final[pl.DataFrame] = time_interval_data.select(
        [
            pl.col("time_since_prev_trade").mean().alias("time_since_prev_mean"),
            pl.col("time_since_prev_trade").var().alias("time_since_prev_var"),
            pl.col("time_since_prev_trade").std().alias("time_since_prev_std"),
            pl.col("time_until_next_trade").mean().alias("time_until_next_mean"),
            pl.col("time_until_next_trade").var().alias("time_until_next_var"),
            pl.col("time_until_next_trade").std().alias("time_until_next_std"),
        ]
    )

    return time_interval_stats


def analyse_trade_quantities(quantities_data: pl.DataFrame) -> pl.DataFrame:
    quantities_stats: t.Final[pl.DataFrame] = quantities_data.select(
        [
            pl.col("quantity").mean().alias("qty_mean"),
            pl.col("quantity").median().alias("qty_median"),
            pl.col("quantity").mode().first().alias("qty_mode"),
            pl.col("quantity").var().alias("qty_var"),
            pl.col("quantity").std().alias("qty_std"),
        ]
    )

    return quantities_stats


def analyse_trade_orders(orders_data: pl.DataFrame) -> pl.DataFrame:
    total_orders, _ = orders_data.shape
    buy_orders: t.Final[int] = int((orders_data["side_heur"] == Order.BUY_ORDER).sum())
    sell_orders: t.Final[int] = int(
        (orders_data["side_heur"] == Order.SELL_ORDER).sum()
    )

    buy_order_rate: t.Final[float] = buy_orders / total_orders
    sell_order_rate: t.Final[float] = sell_orders / total_orders

    return pl.DataFrame(
        {
            "total_orders": total_orders,
            "buy_orders": buy_orders,
            "buy_order_rate": buy_order_rate,
            "sell_orders": sell_orders,
            "sell_order_rate": sell_order_rate,
        }
    )


def analyse_trade_price_streaks(trade_price_data: pl.DataFrame) -> pl.DataFrame:
    is_new_price: t.Final[pl.Series] = trade_price_data["price"] != trade_price_data[
        "price"
    ].shift(1)
    streak_id: t.Final[pl.Series] = is_new_price.cum_sum()
    streaks: t.Final[pl.DataFrame] = (
        trade_price_data.with_columns(streak_id.alias("streak_id"))
        .group_by("streak_id")
        .agg(
            [
                pl.col("price").first().alias("price"),
                pl.count().alias("streak_length"),
            ]
        )
        .select(["price", "streak_length"])
    )

    return streaks


def run_trades_analysis(
    raw_trades_data: TradesDataProcessor, orderbook_data: pl.DataFrame
) -> t.Tuple[TradesAnalysisResult, TradesPlots]:
    trades_data: t.Final[pl.DataFrame] = (
        raw_trades_data.clean()
        .join_select_orderbook_data(orderbook_data)
        .add_time_features()
        .add_price_features()
        .add_buy_sell_heuristic()
        .build()
    )

    time_intervals_stats: t.Final[pl.DataFrame] = analyse_time_intervals(
        trades_data.select(["time_since_prev_trade", "time_until_next_trade"])
    )
    quantities_stats: t.Final[pl.DataFrame] = analyse_trade_quantities(
        trades_data.select("quantity")
    )
    order_side_stats: t.Final[pl.DataFrame] = analyse_trade_orders(
        trades_data.select(["side_heur"])
    )
    trade_price_streaks_stats: t.Final[pl.DataFrame] = analyse_trade_price_streaks(
        trades_data.select(["price"])
    )

    time_interval_prev_plot: t.Final[Plot] = plot_histogram(
        data=trades_data["time_since_prev_trade"].to_numpy(),
        title="Inter-arrival Time Distribution",
        x_title="Time since previous trade",
    )
    time_interval_next_plot: t.Final[Plot] = plot_histogram(
        data=trades_data["time_until_next_trade"].to_numpy(),
        title="Inter-arrival Time Distribution",
        x_title="Time until next trade",
    )
    quantities_plot: t.Final[Plot] = plot_histogram(
        data=trades_data["quantity"].to_numpy(),
        title="Trade quantities distribution",
        x_title="Trade quantity",
    )
    streaks_plot: t.Final[Plot] = plot_histogram(
        data=trade_price_streaks_stats["streak_length"].to_numpy(),
        title="Trade price streak distribution",
        x_title="Streak length",
    )

    plots: t.Final[TradesPlots] = TradesPlots(
        time_interval_until_plt=time_interval_prev_plot,
        time_interval_next_plt=time_interval_next_plot,
        quantities_plt=quantities_plot,
        streaks_plt=streaks_plot,
    )

    return (
        TradesAnalysisResult(
            raw_trades_data=raw_trades_data,
            trades_data=trades_data,
            time_interval_stats=time_intervals_stats,
            quantities_stats=quantities_stats,
            order_side_stats=order_side_stats,
            trade_price_streaks_stats=trade_price_streaks_stats,
        ),
        plots,
    )
