from functools import wraps
from time import time

from src.utils.logger import LOGGER


def timer(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        duration = time() - start
        if duration >= 1:
            LOGGER.warning(
                f"Long execution for {func.__name__}: {duration}.\nInputs (\nargs:\n\t{',\n\t'.join([arg.__name__ for arg in args])}\nkwargs:\n\t{',\n\t'.join([f'{key}: {value}' for key, value in kwargs.items()])})"
            )
        else:
            LOGGER.info(f"Exection time for {func.__name__}: {duration}")

        return result

    return _wrapper
