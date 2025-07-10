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
    max_capacity_profile : TimeDependent
        Time-dependent maximum operational capacity of the component.
    consumes : list[Resource]
        Resources consumed by this component.
    produces : list[Resource]
        Resources produced by this component.
    min_capacity_profile : TimeDependent
        Time-dependent minimum operational capacity; defaults to 0.0 for every timestep.
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
    max_capacity_profile: TimeDependent
    consumes: list[Resource] = field(default_factory=list)
    produces: list[Resource] = field(default_factory=list)
    min_capacity_profile: TimeDependent = field(default_factory=list)
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
        1. Converts max_capacity_profile to a numpy array of floats
        2. Validates max_capacity_profile values
        3. Checks that flexibility is either 'flex' or 'fixed'
        4. Warns if fixed flexibility and min_capacity_profile were both set by the user
        5. Sets min_capacity_profile equal to max_capacity_profile if flexibility is fixed
        6. Populates min_capacity_profile if necessary
        7. Converts min_capacity_profile to a numpy array of floats if necessary
        8. Validates min_capacity_profile values
        9. Verifies all resources are Resource instances
        10. Ensures capacity_resource is in either consumes or produces
        11. Calls _validate_cashflows to validate cashflows

        Raises
        ------
        ValueError
            If any validation check fails
        TypeError
            If resources is not a list of Resource instances
        UserWarning
            If min_capacity_profile and fixed flexibility were both explicitly specified for a component
        """
        # convert max_capacity_profile
        self.max_capacity_profile = np.asarray(self.max_capacity_profile, float).ravel()

        # validate max_capacity_profile
        if (self.max_capacity_profile < 0).any():
            raise ValueError(f"{self.name}: max_capacity_profile contains negative values")

        # flexibility
        if self.flexibility not in ("flex", "fixed"):
            raise ValueError(
                f"{self.name}: flexibility must be 'flex' or 'fixed', got {self.flexibility}"
            )

        if self.flexibility == "fixed":
            if len(self.min_capacity_profile) > 0:
                warnings.warn(
                    f"{self.name}: both min_capacity_profile and fixed flexibility were specified. "
                    "Overriding min_capacity_profile in order to fix profile at max_capacity_profile",
                    UserWarning,
                    stacklevel=2,
                )
            self.min_capacity_profile = self.max_capacity_profile

        if len(self.min_capacity_profile) < 1:
            # set default min_capacity_profile
            self.min_capacity_profile = np.full(len(self.max_capacity_profile), 0.0)
        else:
            # convert min_capacity_profile
            self.min_capacity_profile = np.asarray(self.min_capacity_profile, float).ravel()

            # validate min_capacity_profile
            if len(self.min_capacity_profile) != len(self.max_capacity_profile):
                raise ValueError(
                    f"{self.name}: length of min_capacity_profile does not equal length of max_capacity_profile"
                    f"({len(self.min_capacity_profile)} != {len(self.max_capacity_profile)})"
                )

            for min_cap_value, max_cap_value in zip(
                self.min_capacity_profile, self.max_capacity_profile, strict=True
            ):
                if not (0 <= min_cap_value <= max_cap_value):
                    raise ValueError(
                        f"{self.name}: each value in min_capacity_profile must be in "
                        f"[0, <max_capacity_profile value>] ({min_cap_value} is not in [0, {max_cap_value}])"
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
        self._validate_cashflows()

    def _validate_cashflows(self) -> None:
        """
        Validate cashflows and expand cashflow price_profiles if not provided by the user.

        Raises
        ------
        TypeError:
            If cashflows contains elements that are not CashFlow instances
        ValueError:
            If any cashflow's price_profile is a different length from the component's capacity profile length
        """
        for cf in self.cashflows:
            if not isinstance(cf, CashFlow):
                raise TypeError(f"{self.name}: all cashflows must be CashFlow instances")
            if len(cf.price_profile) < 1:
                cf.price_profile = np.full(len(self.max_capacity_profile), cf.alpha)
            elif len(cf.price_profile) != len(self.max_capacity_profile):
                raise ValueError(
                    f"{self.name}: {cf.name}: cashflow price_profile length "
                    "does not match component profile length!"
                )


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
    consumes : Resource
        The resource type this sink consumes.
    **kwargs : Any
        Additional keyword arguments to pass to the Component parent class.

    Raises
    ------
    ValueError
        If 'produces' or 'capacity_resource' is found in the kwargs

    Notes
    -----
    By default a Sink creates a `RatioTransfer` function with a 1:1 ratio
    using the consumed resource as both input and mocked output.
    """

    def __init__(self, name: str, consumes: Resource, **kwargs: Any) -> None:
        if "produces" in kwargs:
            raise ValueError(
                f"{name}: Keyword argument 'produces' was specified for a Sink, but sinks cannot produce."
                "Please remove keyword argument."
            )

        if "capacity_resource" in kwargs:
            if kwargs["capacity_resource"] == consumes:
                del kwargs["capacity_resource"]
            else:
                raise ValueError(
                    f"{name}: Keyword argument 'capacity_resource' was specified as a different resource "
                    "than the component consumes, which is not permitted for a Sink. Please set "
                    f"'capacity_resource' to {consumes} explicitly, or remove it, and it will be set implicitly."
                )

        super().__init__(name=name, consumes=[consumes], capacity_resource=consumes, **kwargs)

        if self.transfer_fn is None:
            res = consumes
            self.transfer_fn = RatioTransfer(input_resources={res: 1.0}, output_resources={})


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
        utilization between timesteps as a percent of capacity.
        Must be a value between 0 and 1. Default is 1.0 (no limit).
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
        1. Validates ramp_limit and ramp_freq values
        2. If no capacity_resource was provided, attempts to determine one:
           - If the same resource is consumed and produced, uses that resource
           - Otherwise raises an error indicating ambiguity
        3. Warns or raises errors if capacity_resource is ambiguous

        Raises
        ------
        ValueError
            If capacity_resource is ambiguous or missing when required
        UserWarning
            If capacity_resource was not specified but could be determined automatically
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
            If 'max_capacity_profile' is not constant
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

        # Error if max_capacity_profile is not constant
        if not np.all(self.max_capacity_profile == self.max_capacity_profile[0]):
            raise ValueError(
                f"Non-constant max_capacity_profile was added to storage {self.name}. "
                "Storage components must have constant max_capacity_profile values."
            )

        # Set capacity_resource
        self.capacity_resource = self.resource
