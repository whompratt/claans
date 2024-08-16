from functools import wraps
from time import time

from src.utils.logger import LOGGER


def timer(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        LOGGER.debug(f"Execution time for {func.__name__}: {end-start}")
        return result

    return _wrapper
