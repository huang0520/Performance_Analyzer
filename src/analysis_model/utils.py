import logging
from typing import Any, Self


def get_logger() -> logging.Logger:
    return logging.getLogger("main")


class IndexDict(dict):
    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__keys = list(self.keys())

    def get_nth(self: Self, n: int) -> Any:
        return self[self.__keys[n]]
