# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Module
"""

from dataclasses import dataclass, field
from abc import ABC
from typing import Literal, Optional, NewType, Any


@dataclass(frozen=True)
class Resource:
    """ """
    name: str
    unit: Optional[str] = None


@dataclass
class TransferTerm:
    """ """
    coeff: float
    exponent: dict[Resource, int]


@dataclass
class CashFlow:
    """ """
    name: str
    reference_price: float
    reference_driver: float = 1.0
    scaling_factor_x: float = 1.0
    price_is_levelized: bool = False


@dataclass(kw_only=True)
class Component(ABC):
    """
    Represents a system component in the grid analysis. Each component has a
    single "interaction" that describes what it can do (produce, store, demand)
    and a single CashFlowGroup which is a container for component associated cashflows.
    """
    name: str
    capacity_var: Resource
    capacity: float | list[float]
    capacity_factor: float | list[float] | None = None
    minimum: float | list[float] | None = None
    dispatch_flexibility: str = "independent"
    cashflows: list[CashFlow] = field(default_factory=list)
    transfer_terms: list[TransferTerm] = field(default_factory=list)
    levelized_meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """ """
        pass


@dataclass
class Source(Component):
    """ """
    produces: Resource
    tracking_vars: list[str] = field(default_factory=lambda: ["production"])

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        self.transfer_terms = [TransferTerm(1.0, {self.produces: 1})]


@dataclass
class Sink(Component):
    """ """
    consumes: Resource
    tracking_vars: list[str] = field(default_factory=lambda: ["production"])

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        self.transfer_terms = [TransferTerm(-1.0, {self.consumes: 1})]


@dataclass
class Converter(Component):
    """ """
    consumes: list[Resource]
    produces: Resource
    ramp_limit: float = 1.0
    ramp_freq: int = 0
    tracking_vars: list[str] = field(default_factory=lambda: ["production"])


@dataclass
class Storage(Component):
    """ """
    resource: Resource
    rte: float = 1.0
    max_charge_rate: float = 1.0
    max_discharge_rate: float = 1.0
    initial_stored: float = 0
    periodic_level: bool = True
    tracking_vars: list[str] = field(default_factory=lambda: ["level", "charge", "discharge",])

