from sys import stderr

from loguru import logger


def create_logger():
    logger.remove()
    logger.add(stderr, level="INFO")
    return logger


LOGGER = create_logger()
