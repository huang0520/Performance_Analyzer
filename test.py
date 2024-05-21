# %%
import logging.config
from pathlib import Path

import yaml
from analysis_model.intermediate_config.architecture_config import ArchitectueConfig
from analysis_model.intermediate_config.workload_config import WorkloadConfig
from analysis_model.utils import IndexDict
from icecream import ic

logging.config.fileConfig("./logging.conf", disable_existing_loggers=False)

file_dir = Path("./inputs")
output_dir = Path("./outputs")

workload = yaml.safe_load(Path.open(file_dir / "workload.yml"))
architecute = yaml.safe_load(Path.open(file_dir / "architecture.yml"))

workload_config = WorkloadConfig.create(workload)
arch_config = ArchitectueConfig.create(architecute)

ic(arch_config.hierarchy.get_nth(-1))
