from __future__ import annotations

from collections import namedtuple
from typing import Self

from analyzer.IR import ArchitectueConfig

spatial = namedtuple("spatial", ["num_x", "num_y"])


class Dataflow(dict):
    @classmethod
    def create(cls: type[Dataflow], arch: ArchitectueConfig) -> Dataflow:
        dataflow: dict[str, spatial] = {}
        for k, v in arch.hierarchy.items():
            # Create spatial level
            if v.num_x != 1 or v.num_y != 1:
                dataflow[f"{k}_spatial"] = spatial(v.num_x, v.num_y)

            # Create temporal level
            if v.elem_type == "component":
                dataflow[k] = spatial(v.num_x, v.num_y)

        return cls(dataflow)

    def get_levels(self: Self) -> tuple[str]:
        return tuple(self.keys())
