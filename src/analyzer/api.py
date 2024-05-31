from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from yaml import safe_dump, safe_load

from analyzer.dataflow import Dataflow
from analyzer.IR import ArchitectueConfig, MappingConfig, WorkloadConfig
from analyzer.nest_analysis import NestedLoop
from analyzer.network import Network
from analyzer.tile_analysis import analyze_tiling

test_factor = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]]
test_permutations = [
    ["a", "b"],
    ["c", "d"],
    ["e", "f"],
    ["g", "h"],
    ["i", "j"],
    ["k", "l"],
]


def evaluator(
    input_dir: Path,
    factors: Iterable[Iterable[int]],
    permutations: Iterable[Iterable[str]],
) -> int:
    _create_mapping(input_dir, factors, permutations)

    workload = safe_load((input_dir / "workload.yml").open())
    architecute = safe_load((input_dir / "architecture.yml").open())
    mapping = safe_load((input_dir / "mapping.yml").open())

    workload_config = WorkloadConfig.create(workload)
    arch_config = ArchitectueConfig.create(architecute)
    mapping_config = MappingConfig.create(mapping)

    dataflow = Dataflow.create(arch_config)
    nested_loop = NestedLoop.create(dataflow, mapping_config)
    tile_analyze_result = analyze_tiling(dataflow, nested_loop, workload_config, "MM")

    networks = {
        name: Network.create(network, arch_config, workload_config)
        for name, network in arch_config.network.items()
    }

    return sum(
        network.evaluate_latency(tile_analyze_result) for network in networks.values()
    )


def _create_mapping(
    input_dir: Path,
    factors: Iterable[Iterable[int]],
    permutations: Iterable[Iterable[str]],
) -> None:
    mapping = {"mapping": {}}
    targets = ("DRAM", "L2_SRAM", "L1_Tile", "L1_SRAM", "CP", "CP_Reg")

    for lvl_target, lvl_factors, lvl_permutations in zip(
        targets, factors, permutations, strict=True
    ):
        if lvl_target not in {"L1_Tile", "CP"}:
            mapping["mapping"][lvl_target] = {
                "temporal": {
                    "factor": dict(zip(lvl_permutations, lvl_factors, strict=True)),
                    "permutation": lvl_permutations,
                }
            }
        else:
            mapping["mapping"][lvl_target] = {
                "spatial": {
                    "factor": dict(zip(lvl_permutations, lvl_factors, strict=True)),
                    "permutation": lvl_permutations,
                    "split": 999,
                }
            }

    with (input_dir / "mapping.yml").open("w") as f:
        safe_dump(mapping, f, sort_keys=False)


if __name__ == "__main__":
    input_dir = Path("./inputs")
    evaluator(input_dir, test_factor, test_permutations)
