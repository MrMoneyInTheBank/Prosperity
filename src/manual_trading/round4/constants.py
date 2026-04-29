from typing import Final

from src.manual_trading.round4.datatypes import (
    Product,
    Underlying,
    BinaryPut,
    ChooserOption,
    KnockOutPut,
    OptionSide,
    VanillaOption,
)

TRADING_DAYS_PER_YEAR: Final[int] = 252
TRADING_DAYS_PER_WEEK: Final[int] = 5
STEPS_PER_DAY: Final[int] = 4
STEPS_PER_YEAR: Final[int] = STEPS_PER_DAY * TRADING_DAYS_PER_YEAR
AC_VOL_ANNUAL: Final[float] = 2.51

AC_50_C = VanillaOption(strike_price=50, side=OptionSide.CALL)
AC_50_C_2 = VanillaOption(strike_price=50, side=OptionSide.CALL, TTE_weeks=2)
AC_60_C = VanillaOption(strike_price=60, side=OptionSide.CALL)
AC_35_P = VanillaOption(strike_price=35, side=OptionSide.PUT)
AC_40_P = VanillaOption(strike_price=40, side=OptionSide.PUT)
AC_45_P = VanillaOption(strike_price=45, side=OptionSide.PUT)
AC_50_P = VanillaOption(strike_price=50, side=OptionSide.PUT)
AC_50_P_2 = VanillaOption(strike_price=50, side=OptionSide.PUT, TTE_weeks=2)
AC_50_CO = ChooserOption(strike_price=50, decision_time_weeks=2)
AC_40_BP = BinaryPut(strike_price=40, payoff=10)
AC_45_KO = KnockOutPut(strike_price=45, barrier_price=35)

RAW_QUOTES: dict[Product, dict[str, list]] = {
    Underlying.AC: {"bid": [49.975, 200], "ask": [50.025, 200]},
    AC_50_C: {"bid": [12, 50], "ask": [12.05, 50]},
    AC_50_C_2: {"bid": [9.7, 50], "ask": [9.75, 50]},
    AC_60_C: {"bid": [8.8, 50], "ask": [8.85, 50]},
    AC_35_P: {"bid": [4.33, 50], "ask": [4.35, 50]},
    AC_40_P: {"bid": [6.5, 50], "ask": [6.55, 50]},
    AC_45_P: {"bid": [9.05, 50], "ask": [9.1, 50]},
    AC_50_P: {"bid": [12, 50], "ask": [12.05, 50]},
    AC_50_P_2: {"bid": [9.7, 50], "ask": [9.75, 50]},
    AC_50_CO: {"bid": [22.2, 50], "ask": [22.3, 50]},
    AC_40_BP: {"bid": [5, 50], "ask": [5.1, 50]},
    AC_45_KO: {"bid": [0.15, 500], "ask": [0.175, 500]},
}
