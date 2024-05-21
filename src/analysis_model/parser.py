from collections.abc import Mapping
from pathlib import Path
from shutil import copyfileobj
from typing import Any

import yaml
from schema import SchemaError

from analysis_model.validate import _is_input_spec_valid

type InputSpec = Mapping[str, Any]


def parse_input(file_dir: Path, output_dir: Path) -> InputSpec:
    if not isinstance(file_dir, Path):
        msg = "file_dir must be a Path object"
        raise ValueError(msg)
    if not isinstance(output_dir, Path):
        msg = "output_dir must be a Path object"
        raise ValueError(msg)
    if not file_dir.exists():
        msg = f"{file_dir} does not exist"
        raise FileNotFoundError(msg)
    if not output_dir.exists():
        msg = f"{output_dir} does not exist"
        raise FileNotFoundError(msg)

    file_names = ["workload.yml", "arch.yml", "mapping.yml"]
    with Path.open(output_dir / "InputSpec.yml", "wb") as output_file:
        for file_name in file_names:
            with Path.open(file_dir / file_name, "rb") as input_file:
                copyfileobj(input_file, output_file)
            output_file.write(b"\n")

    input_spec = yaml.safe_load(Path.open(output_dir / "InputSpec.yml"))
    if not _is_input_spec_valid(input_spec):
        msg = "Input spec is not valid"
        raise SchemaError(msg)

    return input_spec
