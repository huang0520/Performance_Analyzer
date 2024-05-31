from __future__ import annotations

from typing import Any, Self

from attr import frozen

from analyzer.utils import get_logger

logger = get_logger()


@frozen
class BaseConfig:
    @classmethod
    def create(cls, config: Any) -> Self:  # noqa: ANN102
        cls._pre_validate(config)
        _config = cls._convert(config)
        return cls(**_config)

    @staticmethod
    def _pre_validate(config: Any) -> None:
        pass

    @staticmethod
    def _convert(config: Any) -> Any:
        return config

    def _post_validate(self: Self) -> None:
        pass

    def __attrs_post_init__(self: Self) -> None:
        self._post_validate()
        msg = f"{self.__class__.__name__} created successfully!"
        logger.info(msg)
