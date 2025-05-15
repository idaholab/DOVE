# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.components``
"""

from __future__ import annotations

import warnings
from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

import numpy as np
from numpy.typing import NDArray

from .cashflow import CashFlow
from .transfers import RatioTransfer, TransferFunc

if TYPE_CHECKING:
    from .resource import Resource

TimeDependent: TypeAlias = list[float] | NDArray[np.float64]


@dataclass(kw_only=True)
class Component(ABC):
    """ """

    name: str
    max_capacity: float
    consumes: list[Resource] = field(default_factory=list)
    produces: list[Resource] = field(default_factory=list)
    min_capacity: float = 0.0
    capacity_resource: Resource | None = None
    profile: TimeDependent = field(default_factory=list)
    capacity_factor: bool = False
    flexibility: Literal["flex", "fixed"] = "flex"
    cashflows: list[CashFlow] = field(default_factory=list)
    transfer_fn: TransferFunc | None = None

    @property
    def produces_by_name(self) -> list[str]:
        """ """
        return [r.name for r in self.produces]

    @property
    def consumes_by_name(self) -> list[str]:
        """ """
        return [r.name for r in self.consumes]

    def __post_init__(self) -> None:
        """ """
        # convert profile
        self.profile = np.asarray(self.profile, float).ravel()

        # capacities
        if self.max_capacity < 0:
            raise ValueError(f"{self.name}: max_capacity < 0 ({self.max_capacity})")
        if not (0 <= self.min_capacity <= self.max_capacity):
            raise ValueError(
                f"{self.name}: min_capacity ({self.min_capacity}) must be in [0, {self.max_capacity}]"
            )

        # capacity resource consistency
        if self.capacity_resource:
            allowed = set(self.consumes + self.produces)
            if self.capacity_resource not in allowed:
                raise ValueError(
                    f"{self.name}: capacity_resource {self.capacity_resource} "
                    "not in consumes or produces"
                )

        # profile checks
        if not self.capacity_factor:
            if (self.profile < 0).any():
                raise ValueError(f"{self.name}: profile contains negative values")
        elif ((self.profile < 0) | (self.profile > 1)).any():
            raise ValueError(f"{self.name}: capacity_factor profile must be in [0,1]")

        # flexibility
        if self.flexibility not in ("flex", "fixed"):
            raise ValueError(
                f"{self.name}: flexibility must be 'flex' or 'fixed', got {self.flexibility}"
            )

        # cashflows
        for cf in self.cashflows:
            if not isinstance(cf, CashFlow):
                raise TypeError(f"{self.name}: all cashflows must be CashFlow instances")


@dataclass
class Source(Component):
    """ """

    def __init__(self, name: str, produces: Resource, **kwargs: Any) -> None:
        """ """
        super().__init__(name=name, produces=[produces], capacity_resource=produces, **kwargs)
        if self.transfer_fn is None:
            res = produces
            self.transfer_fn = RatioTransfer(input_res=res, output_res=res, ratio=1.0)


@dataclass
class Sink(Component):
    """ """

    def __init__(self, name: str, consumes: Resource, **kwargs: Any) -> None:
        """ """
        super().__init__(name=name, consumes=[consumes], capacity_resource=consumes, **kwargs)
        if self.transfer_fn is None:
            res = consumes
            self.transfer_fn = RatioTransfer(input_res=res, output_res=res, ratio=1.0)


@dataclass
class Converter(Component):
    """ """

    ramp_limit: float = 1.0
    ramp_freq: int = 0

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        # If no capacity_resource was provided, pick one or error out
        if self.capacity_resource is None and self.consumes and self.produces:
            in_res = self.consumes[0]
            out_res = self.produces[0]
            if in_res is out_res:
                # unambiguous: same resource on both sides
                self.capacity_resource = in_res
                warnings.warn(
                    f"Converter {self.name}: capacity_resource not specified, "
                    f"using common resource '{in_res.name}'.",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                # ambiguous capacity_resource
                if self.transfer_fn is None:
                    raise ValueError(
                        f"Converter {self.name}: ambiguous capacity_resource (consumes {self.consumes_by_name} "
                        f"and produces {self.produces_by_name}) and missing transfer_fn; "
                        "please specify capacity_resource and transfer_fn explicitly."
                    )
                raise ValueError(
                    f"Converter {self.name}: ambiguous capacity_resource (consumes {self.consumes_by_name} "
                    f"and produces {self.produces_by_name}); "
                    "please specify capacity_resource explicitly."
                )


@dataclass
class Storage(Component):
    """ """

    resource: Resource
    rte: float = 1.0
    max_charge_rate: float = 1.0
    max_discharge_rate: float = 1.0
    initial_stored: float = 0.0
    periodic_level: bool = True

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        if self.capacity_resource is None:
            self.capacity_resource = self.resource

        # Error if parameters are outside [0, 1]
        for attr in ("rte", "max_charge_rate", "max_discharge_rate", "initial_stored"):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"Storage {self.name}: '{attr}'={val} is outside the range [0, 1].",
                )
