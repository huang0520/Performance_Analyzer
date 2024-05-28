from pathlib import Path

import yaml
from analyzer.dataflow import Dataflow
from analyzer.IR import (
    ArchitectueConfig,
    MappingConfig,
    WorkloadConfig,
)
from analyzer.nest_analysis import NestedLoop
from analyzer.tile_analysis import analyze_tiling
from attr import asdict
from icecream import ic

file_dir = Path("./inputs")
output_dir = Path("./outputs")

workload = yaml.safe_load(Path.open(file_dir / "workload.yml"))
architecute = yaml.safe_load(Path.open(file_dir / "architecture.yml"))
mapping = yaml.safe_load(Path.open(file_dir / "mapping.yml"))

workload_config = WorkloadConfig.create(workload)
arch_config = ArchitectueConfig.create(architecute)
mapping_config = MappingConfig.create(mapping)

dataflow = Dataflow.create(arch_config)
nested_loop = NestedLoop.create(dataflow, mapping_config)
tile_analyze_result = analyze_tiling(dataflow, nested_loop, workload_config, "MM")

for level in dataflow:
    ic(level)
    ic(dataflow[level])
    ic(nested_loop.get_level_loops(level))
    ic(tile_analyze_result.tile_sizes[level])
    ic(tile_analyze_result.tile_iterations[level])
    ic(tile_analyze_result.tile_accesses[level])
