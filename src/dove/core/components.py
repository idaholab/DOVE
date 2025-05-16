# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.components``
========================

Module containing component classes that form the basis of DOVE models.

The module defines the base `Component` class and its specializations:
- `Source`: generates a resource
- `Sink`: consumes a resource
- `Converter`: consumes, transforms, and produces resources from one type to another
- `Storage`: stores and releases resources over time

Components are connected through resources they consume and produce, forming
a directed graph that represents a system model. Each component can have
associated cash flows to motivate the optimization and transfer functions that define
how resources flow through the component.

Classes:
    Component: Abstract base class for all components in a DOVE model
    Source: Component that produces a resource
    Sink: Component that consumes a resource
    Converter: Component that transforms input resources into output resources
    Storage: Component that can store a resource for later use

Types:
    TimeDependent: Type alias for time series data (list of floats or NumPy array)
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
    """
    A base component class for energy system modeling.

    This abstract class defines the common interface and validation for components
    in an energy system. Components have capacity constraints, can consume and produce
    resources, may have time-dependent profiles, and can have associated cashflows.

    Attributes
    ----------
    name : str
        Unique identifier for the component.
    max_capacity : float
        Maximum operational capacity of the component.
    consumes : list[Resource]
        Resources consumed by this component.
    produces : list[Resource]
        Resources produced by this component.
    min_capacity : float
        Minimum operational capacity, defaults to 0.0.
    capacity_resource : Resource | None
        The resource that defines capacity, if any.
    profile : TimeDependent
        Time-dependent profile for operation, as a numpy array.
    capacity_factor : bool
        Whether the profile represents a capacity factor (0-1)
        rather than absolute values.
    flexibility : Literal["flex", "fixed"]
        Whether the component's operation is flexible or fixed in optimization.
    cashflows : list[CashFlow]
        Economic cashflows associated with this component.
    transfer_fn : TransferFunc | None
        Function defining resource conversion logic.

    Notes
    -----
    This is an abstract base class that should be subclassed to implement
    specific component types like generators, grids, storage, etc.
    """

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
        """A list of resource names that are produced by this component."""
        return [r.name for r in self.produces]

    @property
    def consumes_by_name(self) -> list[str]:
        """A list of resource names that are consumed by this component."""
        return [r.name for r in self.consumes]

    def __post_init__(self) -> None:
        """
        Validate and process the component's attributes after initialization.

        This method performs various checks and conversions to ensure the component is properly configured:
        1. Converts profile to a numpy array of floats
        2. Validates capacity constraints (min/max)
        3. Ensures capacity_resource is in either consumes or produces
        4. Validates profile values based on capacity_factor setting
        5. Checks that flexibility is either 'flex' or 'fixed'
        6. Verifies all cashflows are CashFlow instances

        Raises
        ------
        ValueError
            If any validation check fails
        TypeError
            If cashflows contains elements that are not CashFlow instances
        """
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
    """
    A Source component that produces a specified resource in the DOVE simulation.

    This component acts as a resource generator or provider in the system simulation,
    producing a specific resource type with a configurable capacity.

    Parameters
    ----------
    name : str
        The unique identifier for this source component.
    produces : Resource
        The resource type that this source generates.
    **kwargs : Any
        Additional arguments to pass to the parent Component class.

    Notes
    -----
    By default, a Source uses a RatioTransfer function with a 1:1 ratio,
    meaning it will output the same amount of resource as requested
    (up to its capacity limit).
    """

    def __init__(self, name: str, produces: Resource, **kwargs: Any) -> None:
        super().__init__(name=name, produces=[produces], capacity_resource=produces, **kwargs)
        if self.transfer_fn is None:
            res = produces
            self.transfer_fn = RatioTransfer(input_res=res, output_res=res, ratio=1.0)


@dataclass
class Sink(Component):
    """
    A component that consumes a resource and acts as an endpoint in the DOVE system.

    A Sink is a specialized Component that only consumes resources without producing any.
    It represents destinations where resources exit the system, such as exporters,
    consumers, or terminal points in a resource flow network.

    Parameters
    ----------
    name : str
        The unique identifier for this sink component.
    consumes : Resource
        The resource type this sink consumes.
    **kwargs : Any
        Additional keyword arguments to pass to the Component parent class.

    Notes
    -----
    By default a Sink uses a `RatioTransfer` function with a 1:1 ratio is created
    using the consumed resource as both input and mocked output.
    """

    def __init__(self, name: str, consumes: Resource, **kwargs: Any) -> None:
        super().__init__(name=name, consumes=[consumes], capacity_resource=consumes, **kwargs)
        if self.transfer_fn is None:
            res = consumes
            self.transfer_fn = RatioTransfer(input_res=res, output_res=res, ratio=1.0)


@dataclass
class Converter(Component):
    """
    A Component subclass that converts resources from one type to another.

    The Converter class represents components that consume one set of resources and
    produce another, potentially different set of resources.

    Parameters
    ----------
    ramp_limit : float
        Maximum rate of change for the component's capacity
        utilization between timesteps. Default is 1.0 (no limit).
    ramp_freq : int
        Frequency at which ramp limitations are applied.
        Default is 0 (every timestep).
    **kwargs : Any
        Additional keyword arguments to pass to the parent Component class.

    Notes
    -----
    - A Converter requires a 'capacity_resource' to determine its capacity limits.
    - If not specified, the capacity_resource will be automatically determined:
      - If the component consumes and produces the same resource, that resource is used.
      - Otherwise, capacity_resource must be explicitly specified.
    - When resources differ between input and output, a transfer_fn is required to
      define the conversion relationship.
    """

    ramp_limit: float = 1.0
    ramp_freq: int = 0

    def __post_init__(self) -> None:
        """
        Perform post-initialization validation and setup.

        This method calls the parent class's post-initialization and then:
        1. If no capacity_resource was provided, attempts to determine one:
           - If the same resource is consumed and produced, uses that resource
           - Otherwise raises an error indicating ambiguity
        2. Warns or raises errors if capacity_resource is ambiguous and/or transfer_fn is missing

        Raises
        ------
        ValueError
            If capacity_resource is ambiguous or missing when required
        UserWarning
            If capacity_resource was not specified but could be determined automatically
        """
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
    """
    Storage component for modeling energy storage systems.

    This class represents a storage component in the energy system, capable
    of charging and discharging a specific resource.

    Attributes
    ----------
    resource : Resource
        The resource type that this storage can store.
    rte : float
        Round-trip efficiency, between 0 and 1. Defaults to 1.0.
    max_charge_rate : float
        Maximum charge rate as a fraction of capacity per time period,
        between 0 and 1. Defaults to 1.0.
    max_discharge_rate : float
        Maximum discharge rate as a fraction of capacity per time period,
        between 0 and 1. Defaults to 1.0.
    initial_stored : float
        Initial stored amount as a fraction of capacity,
        between 0 and 1. Defaults to 0.0.
    periodic_level : bool
        If True, storage level at the end of the simulation
        must equal the initial level. Defaults to True.
    **kwargs : Any
        Additional keyword arguments to pass to the parent Component class.
        It's important to note that some Component attributes may not be
        applicable to Storage components, such as `produces`, `consumes`,
        and `capacity_resource`. These attributes are set automatically
        based on the `resource` parameter.

    Notes
    -----
    Storage components are treated differently from other components in terms of
    capacity and resource management. They can store energy for later use,
    and their operation is governed by the round-trip efficiency (rte) and
    charge/discharge rates.
    """

    resource: Resource
    rte: float = 1.0
    max_charge_rate: float = 1.0
    max_discharge_rate: float = 1.0
    initial_stored: float = 0.0
    periodic_level: bool = True

    def __post_init__(self) -> None:
        """
        Initialize the Storage component after instance creation.

        This method validates input parameters of the Storage component:
        - Sets the capacity_resource to resource if not provided
        - Checks if parameters (rte, max_charge_rate, max_discharge_rate, initial_stored) are within the range [0, 1]
        - Calls the parent class's post-initialization method for additional validation

        Raises
        ------
        ValueError
            If any of the rate parameters are outside the range [0, 1]
        """
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
