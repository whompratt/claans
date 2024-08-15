from functools import wraps
from sys import stderr

from loguru import logger


def create_logger():
    logger.remove()
    logger.add(stderr, level="INFO")
    return logger


def log_crud(func, *, entry=True, exit=True, level="TRACE"):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        _logger = logger.opt(depth=1)
        if entry:
            _logger.log(
                level, "Entering `{}` (args={}, kwargs={})", func.__name__, args, kwargs
            )
        result = func(*args, **kwargs)
        if exit:
            _logger.log(level, "Exiting `{}` (result={})", func.__name__, result)
        return result

    return _wrapper


LOGGER = create_logger()
