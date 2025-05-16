# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.system``
====================

Module containing the System class for modeling energy systems.

The System class forms the central component of DOVE models, connecting
resources and components in a coherent framework for optimization and simulation.
The System manages time series data, component interactions, and provides
methods for building and solving optimization problems.

Classes:
    System: Main class for creating and managing energy system models
"""

from typing import Any, Self

import numpy as np

from dove.models import BUILDER_REGISTRY

from . import Component, Resource, Storage


class System:
    """
    The main class for creating and managing energy system models.

    A System represents a collection of components and resources that form
    an energy system. It provides methods for adding components and resources,
    validating the system configuration, and solving optimization problems.

    Attributes
    ----------
    components : list[Component]
        The components in the system.
    resources : list[Resource]
        The resources in the system.
    time_index : list[int]
        The time periods for simulation.
    comp_map : dict[str, Component]
        A mapping of component names to component objects.
    res_map : dict[str, Resource]
        A mapping of resource names to resource objects.
    """

    def __init__(
        self,
        components: list[Component] | None = None,
        resources: list[Resource] | None = None,
        time_index: list[int] | None = None,
    ) -> None:
        """
        Initialize a System instance.

        Parameters
        ----------
        components : list[Component] | None, optional
            The components to include in the system. If None, an empty list is used.
        resources : list[Resource] | None, optional
            The resources to include in the system. If None, an empty list is used.
        time_index : list[int] | None, optional
            The time periods for simulation. If None, [0] is used.
        """
        self.components: list[Component] = [] if components is None else components
        self.resources: list[Resource] = [] if resources is None else resources
        self.time_index = [0] if time_index is None else time_index
        self.comp_map: dict[str, Component] = {comp.name: comp for comp in self.components}
        self.res_map: dict[str, Resource] = {res.name: res for res in self.resources}
        self._normalize_time_series()

    @property
    def non_storage_comp_names(self) -> list[str]:
        """The names of all non-storage components in the system."""
        return [cn for cn in self.comp_map if not isinstance(self.comp_map[cn], Storage)]

    @property
    def storage_comp_names(self) -> list[str]:
        """The names of all storage components in the system."""
        return [cn for cn in self.comp_map if isinstance(self.comp_map[cn], Storage)]

    def summary(self) -> None:
        """
        Print a summary of the system configuration.

        Displays information about the number and names of components and resources,
        categorizes components into storage and non-storage types, and shows
        the time horizon length.
        """
        info = {
            "num_components": len(self.components),
            "component_names": [c.name for c in self.components],
            "non_storage_components": self.non_storage_comp_names,
            "storage_components": self.storage_comp_names,
            "num_resources": len(self.resources),
            "resource_names": [r.name for r in self.resources],
            "time_horizon": len(self.time_index),
        }
        print(info)

    def verify(self) -> None:
        """
        Verify the integrity of the system.

        Checks for:
        - Uniqueness of component names
        - Uniqueness of resource names
        - Consistency of time series lengths with the system time index

        Raises
        ------
        ValueError
            If any validation check fails:
            - Component names are not unique
            - Resource names are not unique
            - Component profile length doesn't match time index length
            - Cashflow price profile length doesn't match time index length
        """
        # Check for unique component names
        component_names = [comp.name for comp in self.components]
        if len(component_names) != len(set(component_names)):
            raise ValueError("Component names must be unique!")

        # Check for unique resource names
        resource_names = [res.name for res in self.resources]
        if len(resource_names) != len(set(resource_names)):
            raise ValueError("Resource names must be unique!")

        # Check that time index length matches profiles and price profiles
        for comp in self.components:
            if comp.profile and len(comp.profile) != len(self.time_index):
                raise ValueError(
                    f"Component '{comp.name}' has a profile length that does not match the time index length!"
                )
            for cf in comp.cashflows:
                if cf.price_profile and len(cf.price_profile) != len(self.time_index):
                    raise ValueError(
                        f"Component '{comp.name}' has a cashflow price profile length that does not match the time index length!"
                    )

    def add_component(self, comp: Component) -> Self:
        """
        Add a component to the system.

        Parameters
        ----------
        comp : Component
            The component to add.

        Returns
        -------
        Self
            The system instance for method chaining.

        Raises
        ------
        ValueError
            If the component validation fails (via verify method).
        """
        self.components.append(comp)
        self.verify()
        self.comp_map[comp.name] = comp
        return self

    def add_resource(self, res: Resource) -> Self:
        """
        Add a resource to the system.

        Parameters
        ----------
        res : Resource
            The resource to add.

        Returns
        -------
        Self
            The system instance for method chaining.
        """
        self.resources.append(res)
        self.res_map[res.name] = res
        return self

    def build(self) -> None:
        """
        Build the system model.

        This method is intended to construct the necessary optimization problem
        based on the system configuration.

        Raises
        ------
        NotImplementedError
            This method is not yet implemented.
        """
        # TODO: Implement the build method
        raise NotImplementedError("System method 'build' is not yet implemented!")

    def solve(self, model_type: str = "price_taker", **kw: dict[str, Any]) -> Any:
        """
        Solve the system optimization problem.

        Parameters
        ----------
        model_type : str, default="price_taker"
            The type of optimization model to use.
        **kw : dict[str, Any]
            Additional keyword arguments to pass to the solver.

        Returns
        -------
        Any
            The optimization results.

        Raises
        ------
        ValueError
            If the specified model_type is not registered.
        """
        try:
            builder_cls = BUILDER_REGISTRY[model_type]
        except KeyError as err:
            raise ValueError(
                f"Unknown model type: '{model_type}'! Available: {list(BUILDER_REGISTRY)}"
            ) from err

        builder = builder_cls(self)
        builder.build()
        builder.solve(**kw)
        return builder.extract_results()

    def _normalize_time_series(self) -> None:
        """
        Normalize time series data within components.

        This internal method:
        1. Scales capacity factor profiles by max_capacity
        2. Handles fixed flexibility components by setting min_capacity
           equal to max_capacity and creating a constant profile
        3. Expands cashflow price profiles to match the time index length
        """
        # I guess these are all the variables we might expect to be varying over time?
        for comp in self.components:
            if comp.capacity_factor:
                # Means user has supplied a time-series profile to the component
                # that represents the capacity factor
                assert isinstance(comp.profile, np.ndarray)
                comp.profile = comp.profile * comp.max_capacity

            if comp.flexibility == "fixed":
                # TODO: Move these into component constructor
                comp.min_capacity = comp.max_capacity
                comp.profile = np.full(len(self.time_index), comp.max_capacity)

            for cf in comp.cashflows:
                if len(cf.price_profile) < 1:
                    cf.price_profile = np.full(len(self.time_index), cf.alpha)
