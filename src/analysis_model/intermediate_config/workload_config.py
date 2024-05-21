from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Self

from attr import field, frozen
from attr.validators import optional

from analysis_model.utils import get_logger
from analysis_model.validate import validate_all_unique, validate_schema

type projection = list[list[str]]

logger = get_logger()


def convert_operation_dimensions_validate(op_dims: Sequence[str]) -> set[str]:
    try:
        validate_all_unique(None, "operation_dimensions", op_dims)
        logger.debug("Operation_dimensions PASS")
        return set(op_dims)
    except ValueError as e:
        logger.error(e)
        raise e


@frozen
class WorkloadConfig:
    operation_dims: set[str] = field(
        converter=convert_operation_dimensions_validate,
        validator=validate_schema({str}),
    )
    operation_dim_size: dict[str, int] = field(validator=validate_schema({str: int}))
    operation_dataspaces: dict[str, list[projection]] = field(
        validator=validate_schema({str: list[projection]})
    )
    operation_coefs: dict[str, int] = field(
        default=None, validator=optional(validate_schema({str: int}))
    )

    @classmethod
    def create(
        cls: type[WorkloadConfig],
        workload: Mapping[str, Any] | Mapping[str, Mapping[str, Any]],
    ) -> WorkloadConfig:
        _workload: Mapping[str, Any] = workload.get("workload", workload)
        return cls(
            operation_dims=_workload["shape"]["operation_dimensions"],
            operation_coefs=_workload["shape"].get("coefficients"),
            operation_dim_size=_workload["operation_dimension_size"],
            operation_dataspaces=_workload["dataspaces"],
        )

    def __attrs_pre_init__(self: Self) -> None:
        logger.info("Starting to create WorkloadConfig...")

    def __attrs_post_init__(self: Self) -> None:
        logger.info("WorkloadConfig created successfully!")

    @operation_dim_size.validator  # type: ignore
    def __is_key_in_operation_dimensions(
        self: Self, _: str, dimension_size: dict[str, int]
    ) -> None:
        for key in dimension_size:
            if key not in self.operation_dims:
                err_msg = (
                    "Keys in operation_dimension_size must be in operation_dimensions"
                )
                logger.error(err_msg)
                raise ValueError(err_msg)

        logger.debug("Operation_dimension_size PASS")

    @operation_dataspaces.validator  # type: ignore
    def __is_proj_elem_in_dim_coef(
        self: Self, attribute: str, value: dict[str, list[projection]]
    ) -> None:
        if any(
            elem not in self.operation_dims and elem not in self.operation_coefs
            for projections in value.values()
            for projection in projections
            for sublist in projection
            for elem in sublist
        ):
            err_msg = (
                "Each element in projection must be in "
                "operation_dimensions or operation_coefficients"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.debug("Dataspaces PASS")
