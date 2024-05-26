from pathlib import Path

import yaml
from analyzer.dataflow import Dataflow
from analyzer.IR import (
    ArchitectueConfig,
    MappingConfig,
    WorkloadConfig,
)
from analyzer.nest_analysis import NestedLoop
from analyzer.tile_analysis import MMAnalyzer
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
tile_analyzer = MMAnalyzer(dataflow, nested_loop, workload_config)
ic(tile_analyzer.tile_sizes)
