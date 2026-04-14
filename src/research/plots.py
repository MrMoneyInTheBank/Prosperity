import typing as t
from dataclasses import dataclass, fields

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray


@dataclass(frozen=True)
class Plot:
    fig: Figure
    ax: Axes


@dataclass(frozen=True)
class OrderbookPlots:
    midprice_plt: Plot
    microprice_dev_plt: Plot
    imbalance_plt: Plot
    imb_corr_plt: Plot
    microprice_dev_corr_plt: Plot


@dataclass(frozen=True)
class TradesPlots:
    time_interval_until_plt: Plot
    time_interval_next_plt: Plot
    quantities_plt: Plot
    streaks_plt: Plot


@dataclass(frozen=True)
class Plots:
    orderbook: OrderbookPlots
    trades: TradesPlots


def plot_line_chart(
    data: NDArray[np.float64], title: str, x_title: str, y_title: str
) -> Plot:
    fig, ax = plt.subplots()
    ax.plot(data)

    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    ax.set_title(title)

    plt.close(fig)

    return Plot(fig, ax)


def plot_scatter_chart(
    X_data: NDArray[np.float64],
    Y_data: NDArray[np.float64],
    title: str,
    x_title: str,
    y_title: str,
) -> Plot:
    fig, ax = plt.subplots()
    ax.scatter(X_data, Y_data)

    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    ax.set_title(title)

    plt.close(fig)

    return Plot(fig, ax)


def plot_histogram(data: NDArray[np.int64], title: str, x_title: str) -> Plot:
    fig, ax = plt.subplots()
    ax.hist(data)
    ax.set_yscale("log")

    ax.set_xlabel(x_title)
    ax.set_ylabel("Frequency (log)")
    ax.set_title(title)

    plt.close(fig)

    return Plot(fig, ax)


def display_plots(obj: t.Any) -> None:
    from IPython.display import display

    if isinstance(obj, Plot):
        display(obj.fig)
        return

    if hasattr(obj, "__dataclass_fields__"):
        for field in fields(obj):
            display_plots(getattr(obj, field.name))
