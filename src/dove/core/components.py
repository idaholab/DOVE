# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.components``
========================

Module containing component classes that form the basis of DOVE models.

Components are connected through resources they consume and produce, forming
a directed graph that represents a system model. Each component can have
associated cash flows to motivate the optimization and transfer functions that define
how resources flow through the component.

Classes
----------
    - `Component`: Abstract base class for all components in a DOVE model
    - `Source`: Component that produces a resource
    - `Sink`: Component that consumes a resource
    - `Converter`: Component that transforms input resources into output resources
    - `Storage`: Component that can store a resource for later use

Types
----------
    - `TimeDependent`: Type alias for time series data (list of floats or NumPy array)
"""

from __future__ import annotations

import warnings
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

import numpy as np
from numpy.typing import NDArray

from .cashflow import CashFlow
from .resource import Resource
from .transfers import RatioTransfer, TransferFunc

TimeDependent: TypeAlias = list[float] | NDArray[np.float64]


@dataclass(kw_only=True)
class Component(ABC):
    """
    A base component class for energy system modeling.

    This abstract class defines the common interface and validation for components
    in an energy system. Components have time-dependent capacity constraints, can consume and produce
    resources, and can have associated cashflows.

    Attributes
    ----------
    name : str
        Unique identifier for the component.
    installed_capacity : float
        Nameplate capacity of the component.
    capacity_factor : TimeDependent
        Fraction of the installed_capacity that is available to dispatch, by timestep.
    consumes : list[Resource]
        Resources consumed by this component.
    produces : list[Resource]
        Resources produced by this component.
    min_profile : TimeDependent
        Time-dependent minimum allowable activity; defaults to 0.0 for every timestep.
    capacity_resource : Resource | None
        The resource that defines capacity, if any.
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
    installed_capacity: float
    capacity_factor: TimeDependent = field(default_factory=list)
    consumes: list[Resource] = field(default_factory=list)
    produces: list[Resource] = field(default_factory=list)
    min_profile: TimeDependent = field(default_factory=list)
    capacity_resource: Resource | None = None
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
        1. Converts capacity_factor and min_profile to numpy arrays of floats
        2. Checks that installed_capacity is positive
        3. Validates capacity_factor values
        4. Validates min_profile values
        5. Checks that flexibility is either 'flex' or 'fixed'
        6. Warns if fixed flexibility and min_profile were both set by the user
        7. Verifies all resources are Resource instances
        8. Ensures capacity_resource is in either consumes or produces
        9. Checks that all cashflows are CashFlow instances

        Raises
        ------
        ValueError
            If any validation check fails
        TypeError
            If resources or cashflows contains elements of the wrong type
        UserWarning
            If min_profile and fixed flexibility were both explicitly specified for a component
        """
        # convert capacity_factor and min_profile
        self.capacity_factor = np.asarray(self.capacity_factor, float).ravel()
        self.min_profile = np.asarray(self.min_profile, float).ravel()

        # validate installed_capacity
        if self.installed_capacity < 0:
            raise ValueError(
                f"{self.name}: installed_capacity (={self.installed_capacity}) cannot be negative"
            )

        # validate capacity_factor
        for t, cap_factor_val in enumerate(self.capacity_factor):
            if cap_factor_val < 0 or cap_factor_val > 1:
                raise ValueError(
                    f"{self.name}: capacity_factor value at timestep {t} "
                    f"({cap_factor_val}) is not between 0 and 1"
                )

        # validate min_profile
        for t, min_val in enumerate(self.min_profile):
            max_val = self.capacity_at_timestep(t)
            if not (0 <= min_val <= max_val):
                raise ValueError(
                    f"{self.name}: min_profile value at timestep {t} is not between 0 and the "
                    f"component's maximum operational capacity at that timestep "
                    f"({min_val} is not in  [0, {max_val}])"
                )

        # flexibility
        if self.flexibility not in ("flex", "fixed"):
            raise ValueError(
                f"{self.name}: flexibility must be 'flex' or 'fixed', got {self.flexibility}"
            )

        if self.flexibility == "fixed" and len(self.min_profile) > 0:
            warnings.warn(
                f"{self.name}: both min_profile and fixed flexibility were specified. "
                "Ignoring min_profile in order to fix the component's dispatch.",
                UserWarning,
                stacklevel=2,
            )

        # resources
        if not all(isinstance(res, Resource) for res in self.produces + self.consumes):
            raise TypeError(f"{self.name}: all resources must be Resource instances")

        # capacity resource consistency
        if self.capacity_resource:
            allowed = set(self.consumes + self.produces)
            if self.capacity_resource not in allowed:
                raise ValueError(
                    f"{self.name}: capacity_resource {self.capacity_resource} "
                    "not in consumes or produces"
                )

        # cashflows
        if not all(isinstance(cf, CashFlow) for cf in self.cashflows):
            raise TypeError(f"{self.name}: all cashflows must be CashFlow instances")

    def capacity_at_timestep(self, t: int) -> float:
        """The maximum operational capacity at the provided time index t"""
        if len(self.capacity_factor) > 0:
            if t > len(self.capacity_factor) - 1:
                available = (
                    "[0]"
                    if len(self.capacity_factor) == 1
                    else f"[0, {len(self.capacity_factor) - 1}]"
                )
                raise IndexError(
                    f"{self.name}: timestep {t} is outside of range for provided capacity_factor "
                    f"data (available range is {available})"
                )
            return self.installed_capacity * self.capacity_factor[t]
        return self.installed_capacity

    def minimum_at_timestep(self, t: int) -> float:
        """The minimum operational capacity at the provided time index t"""
        if len(self.min_profile) > 0:
            if t > len(self.min_profile) - 1:
                raise IndexError(
                    f"{self.name}: timestep {t} is outside of range for provided min_profile "
                    f"data (available range is [0, {len(self.capacity_factor)}])"
                )
            return self.min_profile[t]
        return 0.0


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

    Raises
    ------
    ValueError
        If 'consumes' or 'capacity_resource' is found in the kwargs

    Notes
    -----
    By default, a Source uses a RatioTransfer function with a 1:1 ratio,
    meaning it will output the same amount of resource as requested
    (up to its capacity limit).
    """

    def __init__(self, name: str, produces: Resource, **kwargs: Any) -> None:
        if "consumes" in kwargs:
            raise ValueError(
                f"{name}: Keyword argument 'consumes' was provided for a Source, but sources cannot consume."
                "Please remove keyword argument."
            )

        if "capacity_resource" in kwargs:
            if kwargs["capacity_resource"] == produces:
                del kwargs["capacity_resource"]
            else:
                raise ValueError(
                    f"{name}: Keyword argument 'capacity_resource' was provided as a different resource "
                    "than the component produces, which is not permitted for a Source. Please set "
                    f"'capacity_resource' to {produces} explicitly, or remove it, and it will be set implicitly."
                )

        super().__init__(name=name, produces=[produces], capacity_resource=produces, **kwargs)

        if self.transfer_fn is None:
            res = produces
            self.transfer_fn = RatioTransfer(input_resources={}, output_resources={res: 1.0})


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
    demand_profile : TimeDependent
        Optional. The maximum amount that this sink can consume, by timestep.
    consumes : Resource
        The resource type this sink consumes.
    **kwargs : Any
        Additional keyword arguments to pass to the Component parent class.

    Raises
    ------
    ValueError
        - If 'produces' is found in the kwargs
        - If 'capacity_resource' was specified as a resource other than that in 'consumes'
        - If the capacity was not specified properly

    Notes
    -----
    To specify capacity, sinks accept exactly one of the following argument combinations:
    - time dependent demand_profile AND NOT installed_capacity AND NOT capacity_factor
    - float installed_capacity AND NOT demand_profile (capacity_factor optional)
    The former option should be used when a total variable demand is known, like for a grid.
    The latter option can be used for sinks with constant demand, or it can be used with
    a time dependent capacity factor to express a variable demand as a ratio of a constant.
    """

    def __init__(
        self,
        name: str,
        consumes: Resource,
        demand_profile: TimeDependent | None = None,
        **kwargs: Any,
    ) -> None:
        self.demand_profile = demand_profile
        if self.demand_profile is not None:
            self.demand_profile = np.asarray(self.demand_profile, float).ravel()

        if "produces" in kwargs:
            raise ValueError(
                f"{name}: Keyword argument 'produces' was specified, but is "
                "not accepted for a Sink. Please remove keyword argument."
            )

        if "capacity_resource" in kwargs and kwargs["capacity_resource"] != consumes:
            raise ValueError(
                f"{name}: Keyword argument 'capacity_resource' was specified as a different "
                "resource than the component consumes, which is not permitted for a Sink. "
                f"Please set 'capacity_resource' to '{consumes}' explicitly, or remove it, and "
                "it will be set implicitly."
            )

        if "installed_capacity" not in kwargs and demand_profile is None:
            raise ValueError(
                f"{name}: Insufficient capacity information provided. Please provide "
                "(1) a demand_profile only, (2) an installed_capacity only, OR "
                "(3) an installed_capacity with a capacity_factor."
            )

        comp_init_kwargs = {"name": name, "consumes": [consumes], "capacity_resource": consumes}
        comp_init_kwargs.update(kwargs)

        if demand_profile is not None:
            bad_kwargs = ["installed_capacity", "capacity_factor"]
            for bad_kwarg in bad_kwargs:
                if bad_kwarg in kwargs:
                    raise ValueError(
                        f"{name}: Keyword arguments 'demand_profile' and '{bad_kwarg}' were both "
                        "specified. This combination is not currently accepted for Sinks. Please "
                        "provide (1) a demand_profile only, (2) an installed_capacity only, OR "
                        "(3) an installed_capacity with a capacity_factor."
                    )

            for t, demand_val in enumerate(demand_profile):
                if demand_val < 0:
                    raise ValueError(
                        f"{name}: demand_profile value at timestep {t} ({demand_val}) is negative"
                    )

            # installed_capacity should never be needed in the model if demand_profile is
            # provided, but it's still required by the Component, so we'll give it a value
            comp_init_kwargs.update({"installed_capacity": np.max(demand_profile)})

        super().__init__(**comp_init_kwargs)

        if self.transfer_fn is None:
            res = consumes
            self.transfer_fn = RatioTransfer(input_resources={res: 1.0}, output_resources={})

    def capacity_at_timestep(self, t: int) -> float:
        """
        Returns the maximum amount that the sink can consume at the given time index t.
        Overload of Component.capacity_at_timestep that incorporates demand profile.
        """
        if self.demand_profile is None:
            return super().capacity_at_timestep(t)

        if t > len(self.demand_profile) - 1:
            raise IndexError(
                f"{self.name}: timestep {t} is outside of range for provided demand_profile "
                f"data (available range is [0, {len(self.demand_profile)}])"
            )

        return self.demand_profile[t]


@dataclass
class Converter(Component):
    """
    A Component subclass that converts resources from one type to another.

    The Converter class represents components that consume one set of resources and
    produce another, different set of resources.

    Parameters
    ----------
    ramp_limit : float
        Maximum rate of change for the component's capacity
        utilization between timesteps as a fraction of installed capacity.
        Must be a value between 0 and 1. Default is 1.0 (no limit).
    ramp_freq : int
        Frequency at which ramp limitations are applied.
        Default is 0 (every timestep).
    **kwargs : Any
        Additional keyword arguments to pass to the parent Component class.

    Notes
    -----
    - A Converter requires an explicitly specified 'capacity_resource', which is
      the resource to which the capacity limits refer.
    """

    ramp_limit: float = 1.0
    ramp_freq: int = 0

    def __post_init__(self) -> None:
        """
        Perform post-initialization validation and setup.

        This method calls the parent class's post-initialization and then:
        1. Validates ramp_limit and ramp_freq values
        2. Raises error if capacity_resource or transfer_fn was not explicitly provided
        3. Raises error if any resource is both an input and an output

        Raises
        ------
        ValueError
            If capacity_resource was not explicitly provided
        """
        super().__post_init__()
        if not (0.0 <= self.ramp_limit <= 1.0):
            raise ValueError(
                f"Converter {self.name}: 'ramp_limit'={self.ramp_limit} is outside the range [0, 1].",
            )
        if self.ramp_freq < 0:
            raise ValueError(
                f"Converter {self.name}: 'ramp_freq'={self.ramp_freq} must be positive"
            )

        for required_kwarg in ["capacity_resource", "transfer_fn"]:
            if not getattr(self, required_kwarg, None):
                raise ValueError(
                    f"Converter {self.name}: Required keyword argument '{required_kwarg}' "
                    f"was not provided. Please specify '{required_kwarg}'."
                )

        for res in self.consumes:
            if res in self.produces:
                raise ValueError(
                    f"Converter {self.name}: Resource '{res.name}' found in both 'consumes' and "
                    "'produces'. This is not yet supported. Please ensure consumed and produced "
                    "resources are distinct."
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
        Maximum charge rate as a fraction of installed capacity
        per time period, between 0 and 1. Defaults to 1.0.
    max_discharge_rate : float
        Maximum discharge rate as a fraction of installed capacity
        per time period, between 0 and 1. Defaults to 1.0.
    initial_stored : float
        Initial stored amount as a fraction of installed capacity,
        between 0 and 1. Defaults to 0.0.
    periodic_level : bool
        If True, storage level at the end of the simulation
        must equal the initial level. Defaults to True.
    **kwargs : Any
        Additional keyword arguments to pass to the parent Component class.
        It's important to note that some Component attributes may not be
        applicable to Storage components, such as `produces`, `consumes`,
        and `capacity_resource`. These attributes are set automatically
        based on the `resource` parameter as necessary.

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
        - Checks that unaccepted attributes for Storage components have not been added
        - Checks if parameters (rte, max_charge_rate, max_discharge_rate, initial_stored) are within the range [0, 1]
        - Calls the parent class's post-initialization method for additional validation
        - Sets the capacity_resource to resource

        Raises
        ------
        ValueError
            If 'produces', 'consumes', or 'capacity_resource' was added
            If 'flexibility' was set to 'fixed'
            If any of the rate parameters are outside the range [0, 1]
        """
        # Error if unaccepted attribute was added
        for bad_attr in ("produces", "consumes", "capacity_resource", "transfer_fn"):
            if getattr(self, bad_attr):
                raise ValueError(
                    f"Unaccepted keyword argument '{bad_attr}' provided to Storage {self.name}. "
                    "Please remove keyword argument."
                )

        # Error if flexibility was set to fixed
        if self.flexibility == "fixed":
            raise ValueError(
                f"Attribute 'flexibility' was set to 'fixed' on Storage {self.name}. "
                "Storage components must be flexible."
            )

        # Error if parameters are outside [0, 1]
        for attr in ("rte", "max_charge_rate", "max_discharge_rate", "initial_stored"):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"Storage {self.name}: '{attr}'={val} is outside the range [0, 1].",
                )

        super().__post_init__()

        # Set capacity_resource
        self.capacity_resource = self.resource
