# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import Any, Self

import numpy as np

from dove.models import BUILDER_REGISTRY

from . import Component, Resource, Storage


class System:
    """ """

    def __init__(
        self,
        components: list[Component] | None = None,
        resources: list[Resource] | None = None,
        time_index: list[int] | None = None,
    ) -> None:
        """ """
        self.components: list[Component] = [] if components is None else components
        self.resources: list[Resource] = [] if resources is None else resources
        self.time_index = [0] if time_index is None else time_index
        self.comp_map: dict[str, Component] = {comp.name: comp for comp in self.components}
        self.res_map: dict[str, Resource] = {res.name: res for res in self.resources}
        self._normalize_time_series()

    @property
    def non_storage_comp_names(self) -> list[str]:
        """A list of system component names that are not storage instances."""
        return [cn for cn in self.comp_map if not isinstance(self.comp_map[cn], Storage)]

    @property
    def storage_comp_names(self) -> list[str]:
        """A list of system component names that are storage instances."""
        return [cn for cn in self.comp_map if isinstance(self.comp_map[cn], Storage)]

    def summary(self) -> None:
        """ """
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
        """Verify the integrity of the system."""
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
        """ """
        self.components.append(comp)
        self.verify()
        self.comp_map[comp.name] = comp
        return self

    def add_resource(self, res: Resource) -> Self:
        """ """
        self.resources.append(res)
        self.res_map[res.name] = res
        return self

    def build(self) -> None:
        """ """
        # TODO: Implement the build method
        raise NotImplementedError("System method 'build' is not yet implemented!")

    def solve(self, model_type: str = "price_taker", **kw: dict[str, Any]) -> Any:
        """ """
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
        """ """

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
