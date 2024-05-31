import logging

from rich.logging import RichHandler


def set_logger() -> None:
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(RichHandler())


def get_logger() -> logging.Logger:
    if "main" not in logging.Logger.manager.loggerDict:
        set_logger()
    return logging.getLogger("main")
