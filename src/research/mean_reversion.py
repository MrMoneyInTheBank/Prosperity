import typing as t

import hurst as h
import numpy as np
import polars as pl
import statsmodels.api as sm
from numpy.typing import NDArray
from statsmodels.tsa.stattools import adfuller

from src.research.results import (
    ADFResult,
    MeanReversionTestResults,
    RegressionResult,
    SubsampledRegressionResults,
)


def prepare_mean_reversion_features(
    df: pl.DataFrame, column: str, skips: t.Literal[0, 5, 10]
) -> pl.DataFrame:
    global_mean: float = t.cast(float, df[column].mean())
    lagged_df = df[::skips] if skips != 0 else df

    if "timestamp" not in df.columns or column not in df.columns:
        raise KeyError(
            f"timestamp/{column} column(s) not in dataframe columns: {df.columns}"
        )

    return lagged_df.with_columns(
        (pl.col(column).shift(-1) - pl.col(column)).alias("impending_change"),
        (pl.col(column) - global_mean).alias("deviation_from_mean"),
    ).drop_nulls(subset=["impending_change"])


def run_regression(
    reg_df: pl.DataFrame, skips: t.Literal[0, 5, 10]
) -> RegressionResult:
    X = reg_df["deviation_from_mean"].to_numpy()
    y = reg_df["impending_change"].to_numpy()

    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    _, beta_1 = model.params
    _, beta_1_p_val = model.pvalues
    _, beta_1_t_val = model.tvalues

    alpha = -beta_1
    alpha_p_val = beta_1_p_val
    alpha_t_val = beta_1_t_val

    residuals: NDArray[np.float64] = model.resid

    return RegressionResult(
        alpha=alpha,
        p_val=alpha_p_val,
        t_val=alpha_t_val,
        residuals=residuals,
        skips=skips,
    )


def test_adf(feature: str, data: NDArray) -> ADFResult:
    p_val = float(adfuller(data)[1])

    return ADFResult(feature, p_val)


def compute_hurst_exponents(
    df: pl.DataFrame, column: str, skip_one: int = 5, skip_two: int = 10
) -> t.Tuple[np.float64, np.float64, np.float64]:
    if column not in df.columns:
        raise KeyError(f"{column} columns not in dataframe columns: {df.columns}")

    hurst_exponent, *_ = h.compute_Hc(df[column].to_numpy())
    hurst_skip_one_exponent, *_ = h.compute_Hc(df[column][::skip_one].to_numpy())
    hurst_skip_two_exponent, *_ = h.compute_Hc(df[column][::skip_two].to_numpy())

    return (
        np.float64(hurst_exponent),
        np.float64(hurst_skip_one_exponent),
        np.float64(hurst_skip_two_exponent),
    )


def run_mean_reversion_test(
    df: pl.DataFrame, column: str
) -> MeanReversionTestResults | None:

    midprice_mean_reversion_stats = run_regression(
        prepare_mean_reversion_features(
            df.select(["timestamp", column]), column=column, skips=0
        ),
        skips=0,
    )
    lagged_5_midprice_mean_reversion_stats = run_regression(
        prepare_mean_reversion_features(
            df.select(["timestamp", column]), column=column, skips=5
        ),
        skips=5,
    )
    lagged_10_midprice_mean_reversion_stats = run_regression(
        prepare_mean_reversion_features(
            df.select(["timestamp", column]), column=column, skips=10
        ),
        skips=10,
    )

    regression_results = SubsampledRegressionResults(
        lag_none=midprice_mean_reversion_stats,
        lag_5=lagged_5_midprice_mean_reversion_stats,
        lag_10=lagged_10_midprice_mean_reversion_stats,
    )

    adf_result = test_adf(column, df[column].to_numpy())

    hurst_exponents = compute_hurst_exponents(df.select(column), column=column)

    return MeanReversionTestResults(
        regression_results=regression_results,
        adf_result=adf_result,
        hurst_exponents=hurst_exponents,
    )
