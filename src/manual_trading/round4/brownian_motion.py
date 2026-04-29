import numpy as np
import numpy.typing as npt

from src.manual_trading.round4.constants import STEPS_PER_YEAR


def generate_price_paths(
    initial_price: float,
    vol: float,
    num_paths: int,
    steps: int,
) -> npt.NDArray[np.float64]:
    dt = 1 / STEPS_PER_YEAR

    Z = np.random.normal(size=(num_paths, steps))

    log_returns = (-0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z

    log_price_paths = np.cumsum(log_returns, axis=1)

    price_paths = initial_price * np.exp(log_price_paths)

    initial_column = np.full((num_paths, 1), initial_price)
    price_paths = np.hstack([initial_column, price_paths])

    return price_paths
