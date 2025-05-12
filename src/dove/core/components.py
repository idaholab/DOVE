# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.components``
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Literal, Optional, TypeAlias

import numpy as np
from numpy.typing import NDArray

TimeDependent: TypeAlias = list[float] | NDArray


@dataclass(frozen=True)
class Resource:
    """
    Represents a unique resource type exchanged by different components.

    Attributes:
    name (str): Unique identifier for the resource.
    unit (Optional[str]): Unit of measurement for the resource. Defaults to None.
    """

    name: str
    unit: Optional[str] = None


@dataclass
class TransferTerm:
    """
    A single term in a transfer function, defined by a scaling coefficient and
    a set of resource-specific exponents.

    Attributes:
    coeff (float):
        Scaling factor for the transfer term.
    exponent (dict[Resource, int]):
        Mapping of each Resource to its integer exponent in this term.
    """

    coeff: float
    exponent: dict[Resource, int]


@dataclass
class CashFlow(ABC):
    """
    Base abstract class representing a recurring cash flow.
    """

    name: str
    price_profile: TimeDependent = field(default_factory=list)
    alpha: float = 1.0
    dprime: float = 1.0
    scalex: float = 1.0
    price_is_levelized: bool = False
    sign: int = 0


@dataclass
class Cost(CashFlow):
    """
    Cost cash flow class.
    """
    sign: int = -1


@dataclass
class Revenue(CashFlow):
    """
    Revenue cash flow.

    Inherits from CashFlow and represents revenue as a positive cash inflow.

    Parameters
    ----------
    sign : int, optional
        Sign of the cash flow. +1 indicates an inflow (revenue). Default is +1.
    """
    sign: int = +1


@dataclass(kw_only=True)
class Component(ABC):
    """ """
    name: str
    profile: TimeDependent = field(default_factory=list)
    max_capacity: float = 1.0
    min_capacity: float = 0.0
    capacity_factor: bool = False
    capacity_resource: Optional[Resource] = None
    flexibility: Literal["flex", "fixed"] = "flex"
    cashflows: list[CashFlow] = field(default_factory=list)
    transfer_terms: list[TransferTerm] = field(default_factory=list)

    def __post_init__(self):
        """ """
        pass


@dataclass
class Source(Component):
    """ """
    produces: Resource

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        if self.capacity_resource is None:
            self.capacity_resource = self.produces
        self.transfer_terms = [TransferTerm(1.0, {self.produces: 1})]


@dataclass
class Sink(Component):
    """ """
    consumes: Resource

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        if self.capacity_resource is None:
            self.capacity_resource = self.consumes
        self.transfer_terms = [TransferTerm(-1.0, {self.consumes: 1})]


@dataclass
class Converter(Component):
    """ """

    consumes: list[Resource]
    produces: list[Resource]
    ramp_limit: float = 1.0
    ramp_freq: int = 0

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        extras = {c for c in self.consumes if c != self.produces}
        if extras and self.capacity_resource is None:
            raise ValueError(
                f"Ambiguity! Converter '{self.name}' consumes: {self.consumes} and "
                f"produces: {self.produces} with no 'capacity_resource' defined!"
            )
        if not extras and self.capacity_resource is None:
            self.capacity_resource = self.produces[0]
        if extras and not self.transfer_terms:
            raise ValueError(
                f"Converter '{self.name}' consumes {self.consumes} but no transfer terms defined!"
            )

        assert self.capacity_resource is not None
        # Auto‐adjust the sign of any transfer term that involves capacity_var:
        for term in self.transfer_terms:
            # Does this term actually involve our capacity resource?
            if term.exponent.get(self.capacity_resource, 0) != 0:
                # If capacity_var is in the consumes list → make coeff negative
                if self.capacity_resource in self.consumes:
                    term.coeff = -abs(term.coeff)
                # Otherwise (it’s a produced resource) → make coeff positive
                else:
                    term.coeff = +abs(term.coeff)


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
