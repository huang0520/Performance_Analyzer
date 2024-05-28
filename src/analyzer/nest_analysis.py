from __future__ import annotations

from collections.abc import Generator
from typing import NamedTuple, Self

from analyzer.dataflow import Dataflow
from analyzer.IR import MappingConfig
from analyzer.utils import get_logger

logger = get_logger()


class Loop(NamedTuple):
    dim: str
    factor: int
    level: str


class NestedLoop(list[Loop]):
    def __init__(self: Self, loops: list[Loop], level_idx: dict[str, int]) -> None:
        super().__init__(loops)
        self._level_idx = level_idx
        msg = f"{self.__class__.__name__} created successfully!"
        logger.info(msg)

    @classmethod
    def create(
        cls: type[NestedLoop], dataflow: Dataflow, mapping: MappingConfig
    ) -> NestedLoop:
        pruned_loop = [
            loop
            for level in dataflow
            for loop in cls._create_level_loops(level, mapping)
        ]
        return cls(pruned_loop, cls._create_level_idx(pruned_loop, dataflow))

    @staticmethod
    def _create_level_loops(
        level: str, mapping: MappingConfig
    ) -> Generator[Loop, None, None]:
        spatial_level = level.endswith("_spatial")
        target = level.removesuffix("_spatial") if spatial_level else level
        mapping_elem = (
            mapping[target].spatial if spatial_level else mapping[target].temporal
        )

        assert mapping_elem is not None
        return (
            Loop(dim, factor, level)
            for dim in mapping_elem.permutation
            if (factor := mapping_elem.factor[dim]) > 1
        )

    @staticmethod
    def _create_level_idx(
        pruned_loops: list[Loop], dataflow: Dataflow
    ) -> dict[str, int]:
        remaining_levels = iter(dataflow.get_levels())

        level_idx = {}
        for idx, loop in enumerate(pruned_loops):
            if loop.level not in level_idx:
                level_idx[loop.level] = idx

        level_idx_iter = iter(level_idx.copy().items())
        it = next(level_idx_iter, None)
        for level in remaining_levels:
            if it is not None and level != it[0]:
                level_idx[level] = it[1]
            else:
                it = next(level_idx_iter, None)

        return level_idx

    def get_level_loops(self: Self, level: str) -> dict[str, Loop]:
        return {loop.dim: loop for loop in self if loop.level == level}

    def get_level_idx(self: Self, level: str) -> int | None:
        return self._level_idx.get(level)
