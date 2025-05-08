# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.components``
"""

from dataclasses import dataclass, field
from abc import ABC
from collections.abc import Sequence
from typing import Literal, Optional


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
class CashFlow(ABC):
    """ """

    name: str
    alpha: float | Sequence[float]
    dprime: float | Sequence[float] = 1.0
    scalex: float | Sequence[float] = 1.0
    price_is_levelized: bool = False


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
    capacity: float | Sequence[float]
    capacity_factor: Optional[float | Sequence[float]] = None
    minimum: Optional[float | Sequence[float]] = None
    capacity_resource: Optional[Resource] = None
    flexibility: Literal["independent", "fixed"] = "independent"
    cashflows: Sequence[CashFlow] = field(default_factory=list)
    transfer_terms: Sequence[TransferTerm] = field(default_factory=list)

    def __post_init__(self) -> None:
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

    consumes: Sequence[Resource]
    produces: Resource
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
            self.capacity_resource = self.produces
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
    initial_stored: float = 0
    periodic_level: bool = True

    def __post_init__(self) -> None:
        """ """
        super().__post_init__()
        if self.capacity_resource is None:
            self.capacity_resource = self.resource
