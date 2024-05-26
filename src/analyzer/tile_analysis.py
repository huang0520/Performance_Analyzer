from math import prod
from typing import Self

from icecream import ic

from analyzer.dataflow import Dataflow
from analyzer.IR import Projection, WorkloadConfig
from analyzer.nest_analysis import NestedLoop


class MMAnalyzer:
    def __init__(
        self: Self,
        dataflow: Dataflow,
        nested_loop: NestedLoop,
        workload: WorkloadConfig,
    ) -> None:
        self._dim_sizes = self.__calc_dim_sizes(
            nested_loop, workload.operation_dimensions, dataflow.get_levels()
        )
        self.tile_sizes = self.__calc_tile_sizes(
            workload.dataspaces, dataflow.get_levels()
        )
        self.tile_accesses = self.__calc_tile_accesses(
            nested_loop, workload.dataspaces, dataflow.get_levels()
        )

    @staticmethod
    def __calc_dim_sizes(
        nested_loop: NestedLoop, dims: set[str], levels: tuple[str]
    ) -> dict[str, dict[str, int]]:
        dim_sizes: dict[str, dict[str, int]] = {}
        for level in levels:
            lower_lvl_loops = nested_loop[nested_loop.get_level_idx(level) :]
            dim_sizes[level] = {
                dim: prod(loop.factor for loop in lower_lvl_loops if loop.dim == dim)
                for dim in dims
            }
        return dim_sizes

    def __calc_tile_sizes(
        self: Self,
        dataspaces: dict[str, list[Projection]],
        levels: tuple[str],
    ) -> dict[str, dict[str, int]]:
        def proj_size(proj: Projection, level_dim_sizes: dict[str, int]) -> int:
            return prod(level_dim_sizes[elem] for elem in proj.get_all_proj_elem())

        tile_sizes = {}
        for level in levels:
            lvl_dim_sizes = self._dim_sizes[level]
            tile_sizes[level] = {
                tile_name: prod(proj_size(proj, lvl_dim_sizes) for proj in tile_projs)
                for tile_name, tile_projs in dataspaces.items()
            }
        return tile_sizes

    @staticmethod
    def __calc_tile_iterations(
        nested_loop: NestedLoop,
        dataspaces: dict[str, list[Projection]],
        levels: tuple[str],
    ) -> dict[str, dict[str, int]]:
        tile_iterations: dict[str, dict[str, int]] = {}
        for level in levels:
            higher_lvl_loops = nested_loop[: nested_loop.get_level_idx(level)]

            lvl_tile_iterations: dict[str, int] = {}
            for tile_name, tile_projs in dataspaces.items():
                related_proj_elems = {
                    elem for proj in tile_projs for elem in proj.get_all_proj_elem()
                }

                ignore_idx = 0
                for r_idx, loop in enumerate(reversed(higher_lvl_loops)):
                    if loop.dim in related_proj_elems and loop.factor != 1:
                        ignore_idx = len(higher_lvl_loops) - r_idx
                        break

                lvl_tile_iterations[tile_name] = prod(
                    loop.factor for loop in higher_lvl_loops[:ignore_idx]
                )
            tile_iterations[level] = lvl_tile_iterations
        return tile_iterations

    def __calc_tile_accesses(
        self: Self,
        nested_loop: NestedLoop,
        dataspaces: dict[str, list[Projection]],
        levels: tuple[str],
    ) -> dict[str, int]:
        tile_accesses = {}
        tile_iterations = self.__calc_tile_iterations(nested_loop, dataspaces, levels)
        for level in levels:
            tile_accesses[level] = {
                tile_name: tile_size * tile_iterations[level][tile_name]
                for tile_name, tile_size in self.tile_sizes[level].items()
            }
        return tile_accesses