from math import prod
from typing import Any, Self, TypeVar

from icecream import ic

from analysis_model import Dataflow, InputSpec, NestedLoop


class GemmTileAnalyser:
    def __init__(
        self: Self, dataflow: Dataflow, nested_loop: NestedLoop, input_spec: InputSpec
    ) -> None:
        self.op_dim = input_spec["workload"]["shape"]["operation_dimensions"]
        self.dataspaces_proj_elem: dict[str, list[str]] = {
            dataspace["name"]: self.__flatten_proj(dataspace["projection"])
            for dataspace in input_spec["workload"]["dataspaces"]
        }
        self.targets = list(dataflow.keys())
        self.__tile_size_analysis(nested_loop)

    @staticmethod
    def __flatten_proj(projections: list[list[list[str]]]) -> list[str]:
        return [elem for proj in projections for sub_proj in proj for elem in sub_proj]

    def __tile_size_analysis(self: Self, nested_loop: NestedLoop) -> None:
        lower_lvl_dim_prod = {
            target: {
                dim: self.__calc_lower_lvl_factor_prod(nested_loop, target, dim)
                for dim in self.op_dim
            }
            for target in self.targets
        }
        self.tile_size = {
            target: self.__calc_tiles_size(lower_lvl_dim_prod[target])
            for target in self.targets
        }

    def __calc_lower_lvl_factor_prod(
        self: Self, nested_loop: NestedLoop, target: str, dim: str
    ) -> int:
        lower_lvl_dim_prod = 1

        for curr_target in reversed(self.targets):
            curr_target_loop = nested_loop.get_target_level_loop(curr_target, dim)
            lower_lvl_dim_prod *= curr_target_loop.factor

            if curr_target == target:
                break

        return lower_lvl_dim_prod

    def __calc_tiles_size(
        self: Self, lower_lvl_dim_prod: dict[str, int]
    ) -> dict[str, int]:
        tiles_size = {}
        for dataspace_name, proj_elems in self.dataspaces_proj_elem.items():
            tile_size = prod([lower_lvl_dim_prod[elem] for elem in proj_elems])
            tiles_size[dataspace_name] = tile_size

        return tiles_size

    def __calc_upper_lvl_dim_mult(
        self: Self, nested_loop: NestedLoop, target: str, dim: str
    ) -> int:
        prev_lvl_dim_mult = 1
        for curr_target in self.targets:
            if curr_target == target:
                break
            curr_target_loop = nested_loop.get_target_level_loop(curr_target, dim)
            prev_lvl_dim_mult *= curr_target_loop.factor

        return prev_lvl_dim_mult

    def get_target_level_size(self: Self, target: str) -> int:
        return sum(self.tile_size[target].values())

    def get_tile_size(self: Self, target: str, dataspace_name: str) -> int:
        return self.tile_size[target][dataspace_name]
