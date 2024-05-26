from __future__ import annotations

from typing import Any, Self

from attr import field, frozen
from schema import Optional, Schema

from analyzer.IR.base_config import BaseConfig
from analyzer.utils import get_logger

logger = get_logger()


@frozen
class WorkloadConfig(BaseConfig):
    operation_dimensions: set[str]
    operation_dimension_size: dict[str, int]
    dataspaces: dict[str, list[Projection]]
    coefficient: dict[str, int] | None = field(default=None)

    @classmethod
    def create(cls: type[WorkloadConfig], workload: dict) -> WorkloadConfig:
        _workload: dict[str, Any] = workload.get("workload", workload)
        return super().create(_workload)

    @staticmethod
    def _pre_validate(workload: dict[str, Any]) -> None:
        Schema(
            {
                "shape": {
                    "operation_dimensions": [str],
                    Optional("coefficient"): {str: int},
                },
                "dataspaces": {str: list[list[list[str]]]},
                "operation_dimension_size": {str: int},
            },
            ignore_extra_keys=True,
        ).validate(workload)

        # Check if all operation dimensions is unique
        seen = set()
        if any(
            dim in seen or seen.add(dim)
            for dim in workload["shape"]["operation_dimensions"]
        ):
            err_msg = "Operation dimensions must be unique"
            logger.error(err_msg)
            raise ValueError(err_msg)

    @staticmethod
    def _convert(workload: dict[str, Any]) -> dict[str, Any]:
        _workload = {}
        _workload["operation_dimensions"] = set(
            workload["shape"]["operation_dimensions"]
        )
        if "coefficients" in workload["shape"]:
            _workload["coefficient"] = workload["shape"]["coefficients"]
        _workload["operation_dimension_size"] = workload["operation_dimension_size"]
        _workload["dataspaces"] = {
            k: [Projection(proj) for proj in v]
            for k, v in workload["dataspaces"].items()
        }
        return _workload

    def _post_validate(self: Self) -> None:
        # Check if all operation dimensions have size
        if any(
            dim not in self.operation_dimension_size
            for dim in self.operation_dimensions
        ):
            err_msg = "All operation dimensions must have size"
            logger.error(err_msg)
            raise ValueError(err_msg)

        # Check if all elements in projection are in op_dims or op_coefs
        flatten_projs = (
            elem
            for projections in self.dataspaces.values()
            for projection in projections
            for sublist in projection
            for elem in sublist
        )
        valid_keys = (
            self.operation_dimensions | self.coefficient.keys()
            if self.coefficient
            else self.operation_dimensions
        )
        if any(elem not in valid_keys for elem in flatten_projs):
            err_msg = (
                "Each element in projection must be in "
                "operation_dimensions or operation_coefficients"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)


class Projection(list[list[str]]):
    def get_all_proj_elem(self: Self) -> set[str]:
        return {elem for sublist in self for elem in sublist}
