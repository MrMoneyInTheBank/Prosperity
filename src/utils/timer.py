import functools as ft
import time
import typing as t

P = t.ParamSpec("P")
R = t.TypeVar("R")


def time_fn_call(fn: t.Callable[P, R]) -> t.Callable[P, R]:
    @ft.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.perf_counter()

        result = fn(*args, **kwargs)

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"Function '{fn.__name__}' executed in {execution_time:.4f} seconds.")
        return result

    return wrapper
