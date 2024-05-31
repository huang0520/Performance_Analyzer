from __future__ import annotations

from typing import Any, Self

from attr import field, frozen
from schema import Optional, Schema

from analyzer.IR.base_config import BaseConfig
from analyzer.utils import get_logger

logger = get_logger()


@frozen
class MappingElem(BaseConfig):
    temporal: TemporalMappingElem | None = field(default=None)
    spatial: SpatialMappingElem | None = field(default=None)
    bypass: BypassMappingElem | None = field(default=None)

    @classmethod
    def create(cls: type[MappingElem], elem: dict[str, Any]) -> MappingElem:
        _elem: dict[str, Any] = elem.get("mapping", elem)
        return super().create(_elem)

    @staticmethod
    def _pre_validate(elem: dict[str, Any]) -> None:
        Schema(
            {
                Optional("temporal"): dict,
                Optional("spatial"): dict,
                Optional("bypass"): dict,
            },
            ignore_extra_keys=True,
        ).validate(elem)

    @staticmethod
    def _convert(
        elem: dict[str, Any],
    ) -> dict[str, TemporalMappingElem | SpatialMappingElem | BypassMappingElem]:
        _elem = {}
        if "temporal" in elem:
            _elem["temporal"] = TemporalMappingElem.create(elem["temporal"])
        if "spatial" in elem:
            _elem["spatial"] = SpatialMappingElem.create(elem["spatial"])
        if "bypass" in elem:
            _elem["bypass"] = BypassMappingElem.create(elem["bypass"])
        return _elem

    def __attrs_post_init__(self: Self) -> None:
        pass


@frozen
class TemporalMappingElem(BaseConfig):
    factor: dict[str, int]
    permutation: list[str]

    @staticmethod
    def _pre_validate(temporal: dict[str, Any]) -> None:
        Schema(
            {
                "factor": dict[str, int],
                "permutation": list[str],
            },
            ignore_extra_keys=True,
        ).validate(temporal)

    def __attrs_post_init__(self: Self) -> None:
        pass


@frozen
class SpatialMappingElem(BaseConfig):
    factor: dict[str, int]
    permutation: list[str]
    on_num_x: set[str]
    on_num_y: set[str]

    @staticmethod
    def _pre_validate(spatial: dict[str, Any]) -> None:
        Schema(
            {
                "factor": dict[str, int],
                "permutation": list[str],
                "split": int,
            },
            ignore_extra_keys=True,
        ).validate(spatial)

    @staticmethod
    def _convert(spatial: dict[str, Any]) -> dict[str, Any]:
        split_idx = min(len(spatial["permutation"]), spatial["split"])
        _spatial = {}
        _spatial["factor"] = spatial["factor"]
        _spatial["permutation"] = spatial["permutation"]
        _spatial["on_num_x"] = set(spatial["permutation"][:split_idx])
        _spatial["on_num_y"] = set(spatial["permutation"][split_idx:])
        return _spatial

    def __attrs_post_init__(self: Self) -> None:
        pass


@frozen
class BypassMappingElem(BaseConfig):
    bypass: set[str]
    keep: set[str]

    @staticmethod
    def _pre_validate(bypass: dict[str, Any]) -> None:
        Schema(
            {"bypass": list[str], "keep": list[str]}, ignore_extra_keys=True
        ).validate(bypass)

    @staticmethod
    def _convert(bypass: dict[str, Any]) -> dict[str, Any]:
        return {
            "bypass": set(bypass["bypass"]),
            "keep": set(bypass["keep"]),
        }

    def __attrs_post_init__(self: Self) -> None:
        pass


class MappingConfig(dict[str, MappingElem]):
    def __init__(self: Self, mapping: dict[str, MappingElem]) -> None:
        super().__init__(mapping)
        msg = f"{self.__class__.__name__} created successfully!"
        logger.info(msg)

    @classmethod
    def create(cls: type[MappingConfig], mapping: dict[str, Any]) -> MappingConfig:
        _mapping: dict[str, Any] = mapping.get("mapping", mapping)
        _mapping = cls._convert(_mapping)
        return cls(_mapping)

    @staticmethod
    def _convert(mapping: dict[str, Any]) -> dict[str, MappingElem]:
        return {
            elem_name: MappingElem.create(elem) for elem_name, elem in mapping.items()
        }
