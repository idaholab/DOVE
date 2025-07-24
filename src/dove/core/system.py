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

Classes
--------
    - `System`: Main class for creating and managing DOVE energy system models.
"""

from __future__ import annotations

from typing import Any, Self

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
        dispatch_window: list[int] | None = None,
    ) -> None:
        """
        Initialize a System instance and validate it.

        Parameters
        ----------
        components : list[Component] | None, optional
            The components to include in the system. If None, an empty list is used.
        resources : list[Resource] | None, optional
            The resources to include in the system. If None, an empty list is used.
        dispatch_window : list[int] | None, optional
            The time indices for simulation. If None, [0] is used.
        """
        self.components: list[Component] = [] if components is None else components
        self.resources: list[Resource] = [] if resources is None else resources
        self.dispatch_window = [0] if dispatch_window is None else dispatch_window
        self.comp_map: dict[str, Component] = {comp.name: comp for comp in self.components}
        self.res_map: dict[str, Resource] = {res.name: res for res in self.resources}

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
            "dispatch_window_length": len(self.dispatch_window),
        }
        print(info)

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
        """
        self.components.append(comp)
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

    def _validate(self) -> None:
        """
        Validate the system.

        Checks that:
        - Component names are unique
        - Resource names are unique
        - Time series data has been provided that covers the dispatch_window
        """
        # Check for unique component names
        component_names = [comp.name for comp in self.components]
        if len(component_names) != len(set(component_names)):
            raise ValueError("Component names must be unique!")

        # Check for unique resource names
        resource_names = [res.name for res in self.resources]
        if len(resource_names) != len(set(resource_names)):
            raise ValueError("Resource names must be unique!")

        # Check that the necessary time series data is available
        time_series_errors = ""
        min_length = max(self.dispatch_window) + 1
        for comp in self.components:
            time_series = {"capacity_factor": comp.capacity_factor, "min_profile": comp.min_profile}
            time_series.update(
                {f"{cf.name} price_profile": cf.price_profile for cf in comp.cashflows}
            )

            for ts_name, ts_data in time_series.items():
                if len(ts_data) > 0 and len(ts_data) < min_length:
                    error_msg = (
                        f"\n{comp.name}: time series data for {ts_name} is of insufficient length "
                        f"to cover the system's dispatch_window ({len(ts_data)} < {min_length})."
                    )
                    time_series_errors += error_msg

        if len(time_series_errors) > 0:
            raise ValueError(time_series_errors)

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
        Validate the final system and solve the system optimization problem.

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
        self._validate()

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
