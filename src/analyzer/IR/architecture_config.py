from __future__ import annotations

from typing import Any, Self

from attr import field, frozen
from schema import Optional, Schema

from analyzer.IR.attributes_config import (
    AttributeFactory,
    ComputeAttributes,
    StorageAttrtributes,
)
from analyzer.IR.base_config import BaseConfig
from analyzer.utils import get_logger

HIERARCHY_ELEM_TYPES = {"component", "container"}
COMPONENT_CLASSES = {"storage", "compute"}
NETWORK_CLASSES = {"network"}

logger = get_logger()


@frozen
class ArchitectueConfig(BaseConfig):
    hierarchy: dict[str, HierarchyElem]
    network: dict[str, NetworkElem]

    @classmethod
    def create(cls: type[ArchitectueConfig], arch: dict[str, Any]) -> ArchitectueConfig:
        _arch: dict[str, Any] = arch.get("architecture", arch)
        return super().create(_arch)

    @staticmethod
    def _pre_validate(arch: dict[str, list[dict[str, Any]]]) -> None:
        Schema({"hierarchy": list, "network": list}, ignore_extra_keys=True).validate(
            arch
        )

    @staticmethod
    def _convert(arch: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        return {
            "hierarchy": {
                elem["name"]: HierarchyElem.create(elem) for elem in arch["hierarchy"]
            },
            "network": {
                elem["name"]: NetworkElem.create(elem) for elem in arch["network"]
            },
        }


@frozen
class HierarchyElem(BaseConfig):
    elem_name: str
    elem_type: str
    elem_class: str | None = field(default=None)
    attributes: StorageAttrtributes | ComputeAttributes | None = field(default=None)
    num_x: int = field(default=1)
    num_y: int = field(default=1)

    def __attrs_post_init__(self: Self) -> None:
        self._post_validate()
        msg = f"{self.__class__.__name__}.{self.elem_name} created successfully!"
        logger.debug(msg)

    @staticmethod
    def _pre_validate(elem: dict[str, Any]) -> None:
        Schema(
            {
                "name": str,
                "type": lambda x: x in HIERARCHY_ELEM_TYPES,
                Optional("class"): lambda x: x in COMPONENT_CLASSES,
                Optional("attributes"): dict,
                Optional("spatial"): dict,
            },
            ignore_extra_keys=True,
        ).validate(elem)

        if elem["type"] == "component" and not any(
            key in elem for key in ("class", "attributes")
        ):
            err_msg = f"{elem["name"]} must have 'class' and 'attributes' keys"
            logger.error(err_msg)
            raise ValueError(err_msg)

    @staticmethod
    def _convert(elem: dict[str, Any]) -> dict[str, Any]:
        _elem = {}
        _elem["elem_name"] = elem["name"]
        _elem["elem_type"] = elem["type"]
        if elem["type"] == "component":
            _elem["elem_class"] = elem["class"]
            _elem["attributes"] = AttributeFactory.create(
                elem["attributes"], elem["class"]
            )
        if "spatial" in elem:
            _elem["num_x"] = elem["spatial"].get("NumX", 1)
            _elem["num_y"] = elem["spatial"].get("NumY", 1)
        return _elem

    def _post_validate(self: Self) -> None:
        if self.elem_type not in HIERARCHY_ELEM_TYPES:
            err_msg = f"{self.elem_name} elem_type must be in {HIERARCHY_ELEM_TYPES}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        if self.elem_type == "container" and any(
            v is not None for v in (self.elem_class, self.attributes)
        ):
            err_msg = f"{self.elem_name} cannot have 'class' and 'attributes' keys"
            logger.error(err_msg)
            raise ValueError(err_msg)


@frozen
class NetworkElem:
    @classmethod
    def create(cls: type[NetworkElem], elem: dict[str, Any]) -> NetworkElem:
        return cls()
