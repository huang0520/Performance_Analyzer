from collections.abc import Iterable, Iterator, Mapping
from typing import NamedTuple, Self

from icecream import ic

from analysis_model.dataflow import Dataflow
from analysis_model.parser import InputSpec

type _ParsedMapping = dict[str, _ParsedMappingElem]


class _ParsedMappingElem(NamedTuple):
    factor: dict[str, int]
    permutation: list[str]


class _Loop(NamedTuple):
    name: str
    factor: int


class NestedLoop:
    def __init__(self: Self, dataflow: Dataflow, input_spec: InputSpec) -> None:
        if not isinstance(dataflow, Dataflow):
            msg = "dataflow must be a Dataflow object"
            raise ValueError(msg)
        if not isinstance(input_spec, Mapping):
            msg = "mapping must be an iterable object"
            raise ValueError(msg)

        parsed_mapping: _ParsedMapping = self.__parse_mapping(input_spec["mapping"])

        self.op_dims = input_spec["workload"]["shape"]["operation_dimensions"]
        self.__nested_loop = self.__gen_nested_loop(
            dataflow, parsed_mapping, self.op_dims
        )
        self.__target_lvl_idxes = {
            target: idx for idx, target in enumerate(reversed(dataflow))
        }

    def __iter__(self: Self) -> Iterator:
        return self.__nested_loop.__iter__()

    def __getitem__(self: Self, key: str) -> int:
        return self.__nested_loop[key]

    def __len__(self: Self) -> int:
        return len(self.__nested_loop)

    def get_target_level_idx(self: Self, target: str) -> int:
        return self.__target_lvl_idxes[target]

    def get_target_level_loops(self: Self, target: str) -> list[_Loop]:
        lvl_idx = self.__target_lvl_idxes[target]
        lvl_loops = [
            _Loop(name.removesuffix(f"_{lvl_idx}"), self.__nested_loop[name])
            for name in self.__nested_loop
            if name.endswith(str(lvl_idx))
        ]
        return lvl_loops

    def get_target_level_loop(self: Self, target: str, op_dim: str) -> _Loop:
        lvl_idx = self.__target_lvl_idxes[target]
        loop_name = f"{op_dim}_{lvl_idx}"
        return _Loop(op_dim, self.__nested_loop[loop_name])

    @staticmethod
    def __gen_nested_loop(
        dataflow: Dataflow,
        parsed_mapping: _ParsedMapping,
        op_dims: list[str],
    ) -> dict[str, int]:
        # Create counter for each operation dimension
        op_dim_counter = {op_dim: len(dataflow) - 1 for op_dim in op_dims}

        nested_loop = {}
        for target in dataflow:
            mapping_elem = parsed_mapping[target]
            for op_dim in mapping_elem.permutation:
                loop_name = f"{op_dim}_{op_dim_counter[op_dim]}"
                nested_loop[loop_name] = mapping_elem.factor[op_dim]
                op_dim_counter[op_dim] -= 1

        return nested_loop

    @staticmethod
    def __parse_mapping(mapping: Iterable) -> _ParsedMapping:
        def transform_map(mapping_map: dict) -> tuple[str, _ParsedMappingElem]:
            if mapping_map["type"] == "temporal":
                target_name = mapping_map["target"]
            elif mapping_map["type"] == "spatial":
                target_name = f"{mapping_map['target']}_spatial"

            return target_name, _ParsedMappingElem(
                mapping_map["factor"], mapping_map["permutation"]
            )

        filtered_mapping = filter(
            lambda x: x["type"] in {"temporal", "spatial"}, mapping
        )
        return dict(map(transform_map, filtered_mapping))
