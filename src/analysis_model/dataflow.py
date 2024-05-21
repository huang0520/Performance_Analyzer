from collections import namedtuple
from collections.abc import Iterable, Iterator, KeysView, Mapping
from typing import Any, Self

from analysis_model.parser import InputSpec


class Dataflow(Mapping):
    def __init__(self: Self, input_spec: InputSpec) -> None:
        if not isinstance(input_spec, dict):
            msg = "spec must be a dictionary object"
            raise ValueError(msg)
        if input_spec.get("architecture") is None:
            msg = "architecture key is required"
            raise ValueError(msg)

        self.__dataflow = self.__gen_dataflow(input_spec["architecture"]["hierarchy"])
        self.__dataflow_keys = list(self.__dataflow.keys())

    def __getitem__(self: Self, key: str | int) -> tuple:
        if isinstance(key, str):
            return self.__dataflow[key]
        elif isinstance(key, int):
            return self.__dataflow[self.__dataflow_keys[key]]

    def __iter__(self: Self) -> Iterator[str]:
        return self.__dataflow.__iter__()

    def __reversed__(self: Self) -> Iterator[str]:
        return self.__dataflow.__reversed__()

    def __len__(self: Self) -> int:
        return len(self.__dataflow)

    def __contains__(self: Self, key: str) -> bool:
        return key in self.__dataflow

    def keys(self: Self) -> KeysView:
        return self.__dataflow.keys()

    def values(self: Self) -> Iterable:
        return self.__dataflow.values()

    def items(self: Self) -> Iterable:
        return self.__dataflow.items()

    def get(self: Self, key: str, default: Any = None) -> tuple | None:
        return self.__dataflow.get(key, default)

    def __repr__(self: Self) -> str:
        return self.__dataflow.__repr__()

    @staticmethod
    def __rm_unsed_add_default_attr(hierarchy_dict: dict[str, Any]) -> dict[str, Any]:
        new_dict: dict[str, Any] = {k: hierarchy_dict.get(k) for k in ["type", "name"]}

        if hierarchy_dict.get("spatial") is None:
            new_dict["spatial"] = {"NumX": 1, "NumY": 1}
        else:
            new_dict["spatial"] = {
                "NumX": hierarchy_dict["spatial"].get("NumX", 1),
                "NumY": hierarchy_dict["spatial"].get("NumY", 1),
            }
        return new_dict

    def __gen_dataflow(self: Self, hierarchy: list[dict[str, Any]]) -> dict[str, tuple]:
        spatial = namedtuple("spatial", ["NumX", "NumY"])
        dataflow: dict[str, tuple] = {}
        prune_hierarchy = [self.__rm_unsed_add_default_attr(h) for h in hierarchy]

        curr_num_x = 1
        curr_num_y = 1
        for i, h in enumerate(prune_hierarchy):
            curr_num_x *= h["spatial"]["NumX"]
            curr_num_y *= h["spatial"]["NumY"]

            if h["spatial"] != {"NumX": 1, "NumY": 1}:
                dataflow[f"{h['name']}_spatial"] = spatial(curr_num_x, curr_num_y)
            if (i != len(prune_hierarchy) - 1) and h["type"] == "component":
                dataflow[h["name"]] = spatial(curr_num_x, curr_num_y)
        return dataflow
