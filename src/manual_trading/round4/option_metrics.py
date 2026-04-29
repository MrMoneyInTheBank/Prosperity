import numpy as np
import numpy.typing as npt

from src.manual_trading.round4.datatypes import (
    BinaryPut,
    ChooserOption,
    KnockOutPut,
    Option,
    OptionSide,
    VanillaOption,
)


def get_payoffs(
    opt: Option,
    price_paths: npt.NDArray,
    last_prices: npt.NDArray,
    two_week_prices: npt.NDArray,
) -> npt.NDArray:
    if isinstance(opt, VanillaOption):
        if opt.TTE_weeks == 3:
            if opt.side == OptionSide.CALL:
                return np.maximum(last_prices - opt.strike_price, 0)
            else:
                return np.maximum(opt.strike_price - last_prices, 0)
        elif opt.TTE_weeks == 2:
            if opt.side == OptionSide.CALL:
                return np.maximum(two_week_prices - opt.strike_price, 0)
            else:
                return np.maximum(opt.strike_price - two_week_prices, 0)
        else:
            raise RuntimeError()
    elif isinstance(opt, BinaryPut):
        return np.where(last_prices <= opt.strike_price, opt.payoff, 0)
    elif isinstance(opt, ChooserOption):
        mask_is_call = two_week_prices > opt.strike_price
        call_payoffs = np.maximum(last_prices - opt.strike_price, 0)
        put_payoffs = np.maximum(opt.strike_price - last_prices, 0)

        return np.where(mask_is_call, call_payoffs, put_payoffs)
    elif isinstance(opt, KnockOutPut):
        min_price_per_path = np.min(price_paths, axis=1)
        knocked_out = min_price_per_path < opt.barrier_price
        put_payoffs = np.maximum(opt.strike_price - last_prices, 0)

        return np.where(knocked_out, 0, put_payoffs)
    else:
        raise RuntimeError()


def get_delta(
    opt: Option,
    price_paths: npt.NDArray,
    last_prices: npt.NDArray,
    two_week_prices: npt.NDArray,
) -> float:
    payoffs = get_payoffs(opt, price_paths, last_prices, two_week_prices)

    delta_estimate = np.cov(last_prices, payoffs)[0, 1] / np.var(last_prices)

    return float(delta_estimate)
