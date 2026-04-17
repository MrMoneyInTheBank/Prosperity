import typing as t

import polars as pl

from src.config.constants import ORDERBOOK_FEATURES
from src.processing.orderbook import OrderBookDataProcessor
from src.research.plots import OrderbookPlots, Plot, plot_line_chart, plot_scatter_chart
from src.research.results import OrderbookAnalysisResult


def run_orderbook_analysis(
    raw_orderbook_data: OrderBookDataProcessor,
) -> t.Tuple[OrderbookAnalysisResult, OrderbookPlots]:
    orderbook_data: t.Final[pl.DataFrame] = (
        raw_orderbook_data.clean()
        .add_microstructure_features()
        .add_price_features()
        .add_depth_features()
        .build()
    )

    orderbook_features_data: t.Final[pl.DataFrame] = orderbook_data.select(
        ["timestamp", *ORDERBOOK_FEATURES]
    )

    orderbook_stats: t.Final[pl.DataFrame] = orderbook_features_data.describe().select(
        pl.all().exclude("timestamp")
    )

    orderbook_corrs: t.Final[pl.DataFrame] = orderbook_features_data.select(
        [
            pl.corr("imbalance", "future_log_returns").alias("imb_corr"),
            pl.corr("microprice_dev", "future_log_returns").alias("micro_corr"),
        ]
    )

    midprice_plot: t.Final[Plot] = plot_line_chart(
        data=orderbook_data["mid_price"].to_numpy(),
        title="Midprice evolution over time",
        x_title="Timestamp",
        y_title="Midprice",
    )

    microprice_dev_plot: t.Final[Plot] = plot_line_chart(
        data=orderbook_data["microprice_dev"].to_numpy(),
        title="Microprice deviation over time",
        x_title="Timestamp",
        y_title="Microprice deviation",
    )

    imbalance_plot: t.Final[Plot] = plot_line_chart(
        data=orderbook_data["imbalance"].to_numpy(),
        title="Imbalance over time",
        x_title="Timestamp",
        y_title="Imbalance",
    )

    imb_corr_plot: t.Final[Plot] = plot_scatter_chart(
        X_data=orderbook_data["imbalance"].to_numpy(),
        Y_data=orderbook_data["future_log_returns"].to_numpy(),
        title="Imbalance vs Future returns",
        x_title="Imabalance",
        y_title="Future returns (log)",
    )

    microprice_dev_corr_plot: t.Final[Plot] = plot_scatter_chart(
        X_data=orderbook_data["microprice_dev"].to_numpy(),
        Y_data=orderbook_data["future_log_returns"].to_numpy(),
        title="Microprice deviation vs Future returns",
        x_title="Microprice deviation",
        y_title="Future returns (log)",
    )

    plots: t.Final[OrderbookPlots] = OrderbookPlots(
        midprice_plt=midprice_plot,
        microprice_dev_plt=microprice_dev_plot,
        imbalance_plt=imbalance_plot,
        imb_corr_plt=imb_corr_plot,
        microprice_dev_corr_plt=microprice_dev_corr_plot,
    )

    return (
        OrderbookAnalysisResult(
            raw_orderbook_data=raw_orderbook_data,
            orderbook_data=orderbook_data,
            orderbook_features_data=orderbook_features_data,
            orderbook_stats=orderbook_stats,
            orderbook_corrs=orderbook_corrs,
        ),
        plots,
    )
