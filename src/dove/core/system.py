# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import Self

import numpy as np

from ..models import BUILDER_REGISTRY
from . import Component, Resource, Storage


class System:
    """ """

    def __init__(self, components=None, resources=None, time_index=None) -> None:
        """ """
        self.components: list[Component] = [] if components is None else components
        self.resources: list[Resource] = [] if resources is None else resources
        self.time_index = [0] if time_index is None else time_index
        self.comp_map = {comp.name: comp for comp in self.components}
        self.res_map = {res.name: res for res in self.resources}
        self._normalize_time_series()

    @property
    def non_storage_comp_names(self) -> list[str]:
        """ """
        return [cn for cn in self.comp_map.keys() if not isinstance(self.comp_map[cn], Storage)]

    @property
    def storage_comp_names(self) -> list[str]:
        """ """
        return [cn for cn in self.comp_map.keys() if isinstance(self.comp_map[cn], Storage)]

    def add_component(self, comp) -> Self:
        """ """
        self.components.append(comp)
        self.comp_map[comp.name] = comp
        return self

    def add_resource(self, res) -> Self:
        """ """
        self.resources.append(res)
        self.res_map[res.name] = res
        return self

    def build(self):
        """ """
        raise NotImplementedError("System method 'build' is not yet implemented!")

    def solve(self, model_type: str = "price_taker", **kw):
        """ """
        try:
            builder_cls = BUILDER_REGISTRY[model_type]
        except KeyError:
            raise ValueError(
                f"Unknown model type: '{model_type}'! Available: {list(BUILDER_REGISTRY)}"
            )

        builder = builder_cls(self)
        builder.build()
        builder.solve()
        return builder.extract_results()

    def _normalize_time_series(self) -> None:
        """ """

        # I guess these are all the variables we might expect to be varying over time?
        for comp in self.components:
            if comp.capacity_factor:
                # Means user has supplied a time-series profile to the component
                # that represents the capacity factor
                comp.profile = comp.profile * comp.max_capacity

            if comp.flexibility == "fixed":
                comp.min_capacity = comp.max_capacity
                comp.profile = np.full(len(self.time_index), comp.max_capacity)

            for cf in comp.cashflows:
                if len(cf.price_profile) < 1:
                    cf.price_profile = np.full(len(self.time_index), cf.alpha)

