from pathlib import Path

import yaml
from analyzer.dataflow import Dataflow
from analyzer.IR import (
    ArchitectueConfig,
    MappingConfig,
    WorkloadConfig,
)
from analyzer.nest_analysis import NestedLoop
from analyzer.network import Network
from analyzer.tile_analysis import analyze_tiling

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

networks = {
    name: Network.create(network, arch_config, workload_config)
    for name, network in arch_config.network.items()
}
for network in networks.values():
    network.evaluate_latency(tile_analyze_result)
