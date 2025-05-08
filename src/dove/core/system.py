# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import Self, Union

import numpy as np

from ..models import BUILDER_REGISTRY
from .components import Component, Resource, Storage

ArrayLike = Union[float, list[float], np.ndarray]


def _broadcast(x: ArrayLike, T: int) -> list[float]:
    """Turn a scalar or length-T list/array into an np.ndarray of length T."""
    if isinstance(x, (int, float)):
        return list(np.full(T, float(x)))
    arr = np.asarray(x, float)
    if arr.shape == (T,):
        return list(arr)
    raise ValueError(f"Expected scalar or length-{T} array, got shape {arr.shape}")


class System:
    """ """

    def __init__(self, components, resources, time_index) -> None:
        """ """
        self.components: list[Component] = components
        self.resources: list[Resource] = resources
        self.time_index = time_index
        self.comp_map = {comp.name: comp for comp in components}
        self.res_map = {res.name: res for res in resources}
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
        return self

    def add_resource(self, res) -> Self:
        """ """
        self.resources.append(res)
        return self

    def build(self):
        """ """
        raise NotImplementedError("System method 'build()' is not yet implemented!")

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

        # I guess these are technically all the variables we might expect
        # to be varying over time?
        for comp in self.components:
            comp.capacity = _broadcast(comp.capacity, len(self.time_index))

            if comp.capacity_factor is not None:
                comp.capacity_factor = _broadcast(comp.capacity_factor, len(self.time_index))

            if comp.flexibility == "fixed":
                comp.minimum = comp.capacity
            elif comp.minimum is not None:
                comp.minimum = _broadcast(comp.minimum, len(self.time_index))
            else:
                comp.minimum = np.zeros(len(self.time_index), dtype=float).tolist()

            for cf in comp.cashflows:
                cf.alpha = _broadcast(cf.alpha, len(self.time_index))
                cf.dprime = _broadcast(cf.dprime, len(self.time_index))
                cf.scalex = _broadcast(cf.scalex, len(self.time_index))
