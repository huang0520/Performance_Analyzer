from collections import namedtuple
from collections.abc import Iterable, KeysView, Mapping
from typing import Any, Self


class Dataflow(Mapping):
    def __init__(self: Self, spec: dict[str, Any]) -> None:
        if not isinstance(spec, dict):
            msg = "spec must be a dictionary object"
            raise ValueError(msg)
        if spec.get("architecture") is None:
            msg = "architecture key is required"
            raise ValueError(msg)

        hierarchy = spec["architecture"]["hierarchy"]
        prune_hierarchy = [self.__rm_unsed_add_default_attr(h) for h in hierarchy]

        self.__dataflow = self.__gen_dataflow(prune_hierarchy)
        self.__dataflow_keys = list(self.__dataflow.keys())

    def __getitem__(self: Self, key: str | int) -> tuple:
        if isinstance(key, str):
            return self.__dataflow[key]
        elif isinstance(key, int):
            return self.__dataflow[self.__dataflow_keys[key]]

    def __iter__(self: Self) -> Iterable:
        return iter(self.__dataflow)

    def __len__(self: Self) -> int:
        return len(self.__dataflow)

    def __contains__(self: Self, __key: object) -> bool:
        return __key in self.__dataflow

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

    @staticmethod
    def __gen_dataflow(hierarchy: list[dict[str, Any]]) -> dict[str, tuple]:
        spatial = namedtuple("spatial", ["NumX", "NumY"])
        dataflow: dict[str, tuple] = {}

        curr_num_x = 1
        curr_num_y = 1
        for i, h in enumerate(hierarchy):
            curr_num_x *= h["spatial"]["NumX"]
            curr_num_y *= h["spatial"]["NumY"]

            if h["spatial"] != {"NumX": 1, "NumY": 1}:
                dataflow[f"{h['name']}_spatial"] = spatial(curr_num_x, curr_num_y)
            if (i != len(hierarchy) - 1) and h["type"] == "component":
                dataflow[h["name"]] = spatial(curr_num_x, curr_num_y)
        return dataflow
