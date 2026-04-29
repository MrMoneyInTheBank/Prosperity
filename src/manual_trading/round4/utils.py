from src.manual_trading.round4.constants import TRADING_DAYS_PER_YEAR, STEPS_PER_DAY


def weeks_to_years(weeks: float) -> float:
    return (weeks * 5) / TRADING_DAYS_PER_YEAR


def steps_for_weeks(weeks: float) -> int:
    return int(round(weeks * 5 * STEPS_PER_DAY))
