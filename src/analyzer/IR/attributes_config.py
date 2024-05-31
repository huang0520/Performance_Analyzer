from __future__ import annotations

from typing import Any, Self

from attr import field, frozen
from schema import Optional, Schema

from analyzer.IR.base_config import BaseConfig


class AttributeFactory:
    @staticmethod
    def create(
        attributes: dict[str, Any], attribute_type: str
    ) -> StorageAttrtributes | ComputeAttributes | NetworkAttributes:
        if attribute_type == "storage":
            return StorageAttrtributes.create(attributes)
        elif attribute_type == "compute":
            return ComputeAttributes.create(attributes)
        elif attribute_type == "network":
            return NetworkAttributes.create(attributes)
        else:
            err_msg = f"Attribute type {attribute_type} not supported"
            raise NotImplementedError(err_msg)


@frozen
class StorageAttrtributes(BaseConfig):
    depth: int
    width: int
    datawidth: int
    shared_bandwidth: int | None = field(default=None)
    read_bandwidth: int | None = field(default=None)
    write_bandwidth: int | None = field(default=None)

    def __attrs_post_init__(self: Self) -> None:
        self._post_validate()

    @staticmethod
    def _pre_validate(attrs: dict[str, Any]) -> None:
        Schema(
            {
                "depth": int,
                "width": int,
                "datawidth": int,
                Optional("shared_bandwidth"): int,
                Optional("read_bandwidth"): int,
                Optional("write_bandwidth"): int,
            },
            ignore_extra_keys=True,
        ).validate(attrs)

    def _post_validate(self: Self) -> None:
        if self.shared_bandwidth is not None:
            if self.read_bandwidth is not None or self.write_bandwidth is not None:
                err_msg = "Shared bandwidth cannot exist with read or write bandwidth"
                raise ValueError(err_msg)
        elif self.read_bandwidth is not None and self.write_bandwidth is not None:
            err_msg = "Read and write bandwidth must exist together"
            raise ValueError(err_msg)


@frozen
class ComputeAttributes(BaseConfig):
    datawidth: int

    def __attrs_post_init__(self: Self) -> None:
        pass

    @staticmethod
    def _pre_validate(attrs: dict[str, int]) -> None:
        Schema({"datawidth": int}, ignore_extra_keys=True).validate(attrs)


@frozen
class NetworkAttributes(BaseConfig):
    datawidth: int

    def __attrs_post_init__(self: Self) -> None:
        pass

    @staticmethod
    def _pre_validate(attrs: dict[str, int]) -> None:
        Schema({"datawidth": int}, ignore_extra_keys=True).validate(attrs)
