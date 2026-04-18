from dataclasses import dataclass, field, fields

import numpy as np
import polars as pl
from numpy.typing import NDArray
from statsmodels.stats.diagnostic import acorr_ljungbox

from src.processing.orderbook import OrderBookDataProcessor
from src.processing.trades import TradesDataProcessor
from src.research.plots import Plots


@dataclass(frozen=True)
class OrderbookAnalysisResult:
    raw_orderbook_data: OrderBookDataProcessor
    orderbook_data: pl.DataFrame
    orderbook_features_data: pl.DataFrame
    orderbook_stats: pl.DataFrame
    orderbook_corrs: pl.DataFrame


@dataclass(frozen=True)
class TradesAnalysisResult:
    raw_trades_data: TradesDataProcessor
    trades_data: pl.DataFrame
    time_interval_stats: pl.DataFrame
    quantities_stats: pl.DataFrame
    order_side_stats: pl.DataFrame
    trade_price_streaks_stats: pl.DataFrame


@dataclass(frozen=True)
class AnalysisResult:
    orderbook_analysis_result: OrderbookAnalysisResult
    trades_analysis_result: TradesAnalysisResult
    plots: Plots


@dataclass(frozen=True)
class RegressionResult:
    alpha: np.float64
    p_val: np.float64
    t_val: np.float64
    residuals: NDArray[np.float64] = field(repr=False)
    skips: int

    @property
    def is_mean_reverting(self) -> str:
        if self.alpha > 0 and self.p_val < 0.05 and abs(self.t_val) > 2:
            return f"midprice ({self.skips} skips) is showing signs of mean reversion"
        else:
            return (
                f"midprice ({self.skips} skips) is not showing signs of mean reversion"
            )

    def test_residuals_autocorr(self) -> pl.DataFrame:
        return pl.from_pandas(acorr_ljungbox(self.residuals, lags=[10], return_df=True))


@dataclass(frozen=True)
class SubsampledRegressionResults:
    lag_none: RegressionResult
    lag_5: RegressionResult
    lag_10: RegressionResult

    def print_summary(self) -> None:
        for f in fields(self):
            print(f"\n{f.name}")
            print(getattr(self, f.name).is_mean_reverting)


@dataclass(frozen=True)
class ADFResult:
    feature: str
    p_val: float

    @property
    def rejects_unit_root(self) -> bool:
        return self.p_val < 0.05

    def __str__(self) -> str:
        if self.rejects_unit_root:
            return f"{self.feature} is stationary"
        else:
            return f"{self.feature} is not stationary"


@dataclass(frozen=True)
class MeanReversionTestResults:
    regression_results: SubsampledRegressionResults
    adf_result: ADFResult
    hurst_exponents: tuple[np.float64, np.float64, np.float64]
