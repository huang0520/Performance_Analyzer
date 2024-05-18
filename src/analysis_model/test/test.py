# %%
from pathlib import Path

import yaml
from analysis_model.parser import SpecParser
from icecream import ic

# %%

file_dir = Path("./inputs")
parser = SpecParser(file_dir)

ic(parser.dataflow)

# %%
