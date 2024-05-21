from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Self

from attr import define, field, frozen
from attr.validators import instance_of, optional


class AttributeFactory:
    @staticmethod
    def create(attributes: Mapping[str, Any], attribute_type: str) -> BaseAttributes:
        if attribute_type == "storage":
            return StorageAttrtributes.create(attributes)
        elif attribute_type == "compute":
            return ComputeAttributes.create(attributes)
        else:
            err_msg = f"Attribute type {attribute_type} not supported"
            raise NotImplementedError(err_msg)


@frozen
class BaseAttributes(ABC):
    @classmethod
    @abstractmethod
    def create(
        cls: type[BaseAttributes], attributes: Mapping[str, Any]
    ) -> BaseAttributes:
        pass


@frozen
class StorageAttrtributes(BaseAttributes):
    depth: int = field(validator=instance_of(int))
    width: int = field(validator=instance_of(int))
    datawidth: int = field(validator=instance_of(int))
    shared_bandwidth: int | None = field(
        default=None, validator=optional(instance_of(int))
    )
    read_bandwidth: int | None = field(
        default=None, validator=optional(instance_of(int))
    )
    write_bandwidth: int | None = field(
        default=None, validator=optional(instance_of(int))
    )

    def __attrs_post_init__(self: Self) -> None:
        """Check combination of bandwidths is valid"""
        shard_bandwidth_exist = self.shared_bandwidth is not None
        read_bandwidth_exist = self.read_bandwidth is not None
        write_bandwidth_exist = self.write_bandwidth is not None

        if shard_bandwidth_exist and read_bandwidth_exist:
            err_msg = "Shared and read bandwidth cannot exist together"
            raise ValueError(err_msg)
        elif shard_bandwidth_exist and write_bandwidth_exist:
            err_msg = "Shared and write bandwidth cannot exist together"
            raise ValueError(err_msg)
        elif not shard_bandwidth_exist and (
            not read_bandwidth_exist or not write_bandwidth_exist
        ):
            err_msg = "Read and write bandwidth must exist together"
            raise ValueError(err_msg)

    @classmethod
    def create(
        cls: type[StorageAttrtributes], attributes: Mapping[str, int]
    ) -> StorageAttrtributes:
        return StorageAttrtributes(
            depth=attributes["depth"],
            width=attributes["width"],
            datawidth=attributes["datawidth"],
            shared_bandwidth=attributes.get("shared_bandwidth"),
            read_bandwidth=attributes.get("read_bandwidth"),
            write_bandwidth=attributes.get("write_bandwidth"),
        )


@frozen
class ComputeAttributes(BaseAttributes):
    datawidth: int = field(validator=instance_of(int))

    @classmethod
    def create(
        cls: type[ComputeAttributes], attributes: Mapping[str, int]
    ) -> ComputeAttributes:
        return ComputeAttributes(datawidth=attributes["datawidth"])
