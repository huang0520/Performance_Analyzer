from collections import namedtuple
from collections.abc import Iterable, KeysView, Mapping
from pathlib import Path
from typing import Any, Self

import yaml
from icecream import ic
from schema import And, Optional, Schema, SchemaError, Use

from analysis_model.dataflow import Dataflow


class SpecParser:
    def __init__(self: Self, file_dir: Path) -> None:
        if not isinstance(file_dir, Path):
            msg = "file_dir must be a Path object"
            raise ValueError(msg)

        file_path: list[Path] = [
            file_dir / "workload.yml",
            file_dir / "arch.yml",
            file_dir / "mapping.yml",
        ]

        for path in file_path:
            if not path.exists():
                msg = f"{path} does not exist"
                raise FileNotFoundError(msg)

        primitive_spec: dict[str, Any] = {}
        for path in file_path:
            primitive_spec |= yaml.safe_load(Path.open(path))

        primitive_spec = self.__schema_validate(primitive_spec)
        self.dataflow = Dataflow(primitive_spec)

    def __schema_validate(self: Self, spec: dict[str, Any]) -> dict[str, Any]:
        schema = Schema({
            "workload": Use(self.__workload_validate),
            "architecture": Use(self.__architecture_validate),
            "mapping": Use(self.__mapping_validate),
        })
        return schema.validate(spec)

    @staticmethod
    def __workload_validate(workload: dict) -> dict:
        schema = Schema({
            "shape": {
                "operation_dimensions": And(len, Schema([str]).validate),
                Optional("coefficients"): [{"name": str, "value": int}],
            },
            "dataspaces": And(
                len, Schema([{"name": str, "projection": [[[str]]]}]).validate
            ),
            "operation_dimension_size": {str: int},
        })
        return schema.validate(workload)

    @staticmethod
    def __architecture_validate(architecture: dict) -> dict:
        def validate_hierarchy_dict(data: dict[str, Any]) -> dict[str, Any]:
            base_schema = {
                "type": lambda x: x in {"component", "container"},
                "name": str,
                Optional("spatial"): {
                    Optional("NumX"): int,
                    Optional("NumY"): int,
                },
                Optional("constrains"): {
                    Optional("dataspace"): {
                        Optional("keep"): [str],
                        Optional("bypass"): [str],
                    },
                    Optional("temporal"): {
                        Optional("factor"): {str: int},
                        Optional("permutation"): [str],
                    },
                    Optional("spatial"): {
                        "factor": {str: int},
                        "permutation": [str],
                        "split": int,
                    },
                },
            }
            component_schema = {
                **base_schema,
                "class": str,
                "attributes": {str: object},
            }

            match data.get("type"):
                case "component":
                    data = Schema(component_schema).validate(data)
                case "container":
                    data = Schema(base_schema).validate(data)
                case _:
                    msg = "type is required and must be either component or container"
                    raise SchemaError(msg)
            return data

        schema = Schema({
            "hierarchy": [Use(validate_hierarchy_dict)],
            "network": [
                {
                    "name": str,
                    "class": str,
                    "source": [str],
                    "sink": [str],
                    Optional("allow_pass"): [str],
                    "attributes": {str: object},
                }
            ],
        })
        return schema.validate(architecture)

    @staticmethod
    def __mapping_validate(mapping: list[dict]) -> list[dict]:
        def validate_mapping_dict(data: dict[str, Any]) -> dict[str, Any]:
            base_schema = {
                "target": str,
                "type": lambda x: x in {"dataspace", "temporal", "spatial"},
            }
            dataspace_schema = {**base_schema, "keep": [str], "bypass": [str]}
            temporal_schema = {
                **base_schema,
                "factor": {str: int},
                "permutation": [str],
            }
            spatial_schema = {
                **base_schema,
                "factor": {str: int},
                "permutation": [str],
                "split": int,
            }

            match data.get("type"):
                case "dataspace":
                    data = Schema(dataspace_schema).validate(data)
                case "temporal":
                    data = Schema(temporal_schema).validate(data)
                case "spatial":
                    data = Schema(spatial_schema).validate(data)
                case _:
                    msg = "type is required and must be either dataspace, temporal or spatial"  # noqa: E501
                    raise SchemaError(msg)
            return data

        schema = Schema([Use(validate_mapping_dict)])
        return schema.validate(mapping)
