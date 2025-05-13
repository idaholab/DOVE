# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.components``
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import Literal, Optional, TypeAlias

from numpy.typing import NDArray

from .transfers import RatioTransfer, PolynomialTransfer

TimeDependent: TypeAlias = list[float] | NDArray


@dataclass(frozen=True)
class Resource:
    """ """

    name: str
    unit: Optional[str] = None


@dataclass
class CashFlow(ABC):
    """ """

    name: str
    price_profile: TimeDependent = field(default_factory=list)
    alpha: float = 1.0
    dprime: float = 1.0
    scalex: float = 1.0
    price_is_levelized: bool = False
    sign: int = 0


@dataclass
class Cost(CashFlow):
    """ """

    sign: int = -1


@dataclass
class Revenue(CashFlow):
    """ """

    sign: int = +1


@dataclass(kw_only=True)
class Component(ABC):
    """ """

    name: str
    consumes: list[Resource] = field(default_factory=list)
    produces: list[Resource] = field(default_factory=list)
    max_capacity: float = 1.0
    min_capacity: float = 0.0
    capacity_resource: Optional[Resource] = None
    profile: TimeDependent = field(default_factory=list)
    capacity_factor: bool = False
    flexibility: Literal["flex", "fixed"] = "flex"
    cashflows: list[CashFlow] = field(default_factory=list)
    transfer_fn: Optional[TransferFunc] = None

    @property
    def produces_by_name(self) -> list[str]:
        """ """
        return [r.name for r in self.produces]
    
    @property
    def consumes_by_name(self) -> list[str]:
        """ """
        return [r.name for r in self.consumes]

    def __post_init__(self):
        """ """
        pass


@dataclass
class Source(Component):
    """ """

    def __init__(self, name: str, produces: Resource, **kwargs):
        """ """
        super().__init__(name=name, produces=[produces], capacity_resource=produces, **kwargs)
        if self.transfer_fn is None:
            res = produces.name
            self.transfer_fn = RatioTransfer(input_res=res, output_res=res, ratio=1.0)


@dataclass
class Sink(Component):
    """ """

    def __init__(self, name: str, consumes: Resource, **kwargs):
        """ """
        super().__init__(name=name, consumes=[consumes], capacity_resource=consumes, **kwargs)
        if self.transfer_fn is None:
            res = consumes.name
            self.transfer_fn = RatioTransfer(input_res=res, output_res=res, ratio=1.0)


@dataclass
class Converter(Component):
    """ """
    ramp_limit: float = 1.0
    ramp_freq: int = 0


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
