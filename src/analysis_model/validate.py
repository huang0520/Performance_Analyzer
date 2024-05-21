from collections.abc import Callable, Mapping
from typing import Any

from icecream import ic
from schema import And, Optional, Schema


def _is_input_spec_valid(input_spec: Mapping) -> bool:
    # Check schema
    schema = Schema({
        "workload": _is_workload_schema_valid,
        "architecture": _is_arch_schema_valid,
        "mapping": _is_mapping_schema_valid,
    })
    valid = schema.is_valid(input_spec)

    # Check content
    valid = valid and _is_workload_content_valid(input_spec["workload"])
    return valid


def _is_workload_schema_valid(workload: Mapping) -> bool:
    schema = Schema({
        "shape": {
            "operation_dimensions": And(len, Schema([str]).is_valid),
            Optional("coefficients"): [{"name": str, "value": int}],
        },
        "dataspaces": And(
            len, Schema([{"name": str, "projection": [[[str]]]}]).is_valid
        ),
        "operation_dimension_size": {str: int},
    })
    return schema.is_valid(workload)


def _is_arch_schema_valid(arch: Mapping) -> bool:
    def is_hierarchy_maps_valid(data: Mapping[str, Any]) -> bool:
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
                valid = Schema(component_schema).is_valid(data)
            case "container":
                valid = Schema(base_schema).is_valid(data)
            case _:
                valid = False
        return valid

    schema = Schema({
        "hierarchy": [is_hierarchy_maps_valid],
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
    return schema.is_valid(arch)


def _is_mapping_schema_valid(mapping: Mapping) -> bool:
    def is_mapping_maps_valid(data: Mapping[str, Any]) -> bool:
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
                valid = Schema(dataspace_schema).is_valid(data)
            case "temporal":
                valid = Schema(temporal_schema).is_valid(data)
            case "spatial":
                valid = Schema(spatial_schema).is_valid(data)
            case _:
                valid = False
        return valid

    schema = Schema([is_mapping_maps_valid])
    return schema.is_valid(mapping)


def _is_workload_content_valid(workload: Mapping) -> bool:
    operation_dimensions = workload["shape"]["operation_dimensions"]
    coefficients = workload["shape"].get("coefficients", [])
    valid_elem = operation_dimensions + coefficients

    # Flatten the elements in the dataspace projection
    elems = [
        elem
        for dataspace in workload["dataspaces"]
        for projection in dataspace["projection"]
        for sublist in projection
        for elem in sublist
    ]

    dim_with_size = workload["operation_dimension_size"].keys()

    return all(elem in valid_elem for elem in elems) and all(
        dim in dim_with_size for dim in operation_dimensions
    )


def validate_schema(schema: Any) -> Callable[[Any, Any, Any], None]:
    def _validate_schema(instance: Any, attribute: Any, value: Any) -> None:
        Schema(schema).validate(value)

    return _validate_schema


def validate_all_unique(instance: Any, attribute: Any, value: Any) -> None:
    seen = set()
    if any(x in seen or seen.add(x) for x in value):
        err_msg = f"Each element in {attribute} must be unique"
        raise ValueError(err_msg)
