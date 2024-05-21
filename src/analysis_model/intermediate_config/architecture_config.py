from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Self

from attr import define, field, frozen
from attr.validators import in_, instance_of, optional
from icecream import ic

from analysis_model.intermediate_config.attributes_config import (
    AttributeFactory,
    BaseAttributes,
)
from analysis_model.utils import IndexDict, get_logger
from analysis_model.validate import validate_all_unique, validate_schema

HIERARCHY_ELEM_CLASSES = {"storage", "compute"}
NETWORK_CLASSES = {"network"}

logger = get_logger()


def convert_arch_elem_validate(
    elem_key: str,
) -> Callable[[Sequence[Mapping[str, Any]]], IndexDict]:
    def _convert_arch_elem_validate(
        arch_elem: Sequence[Mapping[str, Any]],
    ) -> IndexDict:
        if elem_key not in {"hierarchy", "network"}:
            err_msg = "Architecture only support 'hierarchy' and 'network' keys"
            logger.error(err_msg)
            raise ValueError(err_msg)

        validate_schema(list[dict])(None, None, arch_elem)
        msg = f"{elem_key} schema PASS"
        logger.debug(msg)

        validate_all_unique(
            None, f"{elem_key}_name", (elem["name"] for elem in arch_elem)
        )

        _hierarchy = {}
        for elem in arch_elem:
            _hierarchy[elem["name"]] = HierarchyElem.create(elem)
            msg = f"{elem_key} element {elem['name']} PASS"
            logger.debug(msg)
        return IndexDict(_hierarchy)

    return _convert_arch_elem_validate


@frozen
class ArchitectueConfig:
    hierarchy: IndexDict = field(converter=convert_arch_elem_validate("hierarchy"))
    network: dict[str, Any] = field()

    def __attrs_pre_init__(self: Self) -> None:
        logger.info("Starting to create ArchitectureConfig...")

    def __attrs_post_init__(self: Self) -> None:
        logger.info("ArchitectureConfig created successfully!")

    @classmethod
    def create(
        cls: type[ArchitectueConfig], architecture: Mapping[str, Any]
    ) -> ArchitectueConfig:
        _architecture: Mapping[str, Any] = architecture.get(
            "architecture", architecture
        )
        return cls(
            hierarchy=_architecture["hierarchy"], network=_architecture["network"]
        )


@define
class HierarchyElem:
    elem_type: str = field(validator=in_({"component", "container"}))
    num_x: int = field(validator=instance_of(int))
    num_y: int = field(validator=instance_of(int))
    elem_class: str | None = field(
        default=None, validator=optional(in_(HIERARCHY_ELEM_CLASSES))
    )
    attributes: BaseAttributes | None = field(
        default=None, validator=optional(instance_of(BaseAttributes)), repr=False
    )

    @elem_class.validator  # type: ignore
    def __is_class_none_if_container(self: Self, _: Any, value: str) -> None:
        if self.elem_type == "container" and value is not None:
            err_msg = "Container elements cannot have 'class' key"
            logger.error(err_msg)
            raise ValueError(err_msg)

    @attributes.validator  # type: ignore
    def __is_attrs_none_if_container(self: Self, _: Any, value: BaseAttributes) -> None:
        if self.elem_type == "container" and value is not None:
            err_msg = "Container elements cannot have 'attributes' key"
            logger.error(err_msg)
            raise ValueError(err_msg)

    @classmethod
    def create(cls: type[HierarchyElem], elem: Mapping[str, Any]) -> HierarchyElem:
        elem_class = elem.get("class")
        attrs = elem.get("attributes")
        if attrs:
            validate_schema({str: object})(None, None, attrs)
        if elem_class and attrs:
            attrs = AttributeFactory.create(attrs, elem_class)

        num_x = spatial.get("NumX", 1) if (spatial := elem.get("spatial")) else 1
        num_y = spatial.get("NumY", 1) if (spatial := elem.get("spatial")) else 1

        return cls(
            elem_type=elem["type"],
            elem_class=elem_class,
            num_x=num_x,
            num_y=num_y,
            attributes=attrs,
        )
