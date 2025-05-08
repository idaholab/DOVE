# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import Self, Union
import numpy as np
import pyomo.environ as pyo
from .pyomo_model_builder import PyomoModelBuilder
from .components import Component, Resource

ArrayLike = Union[float, list[float], np.ndarray]

def _broadcast(x: ArrayLike, T: int) -> np.ndarray:
    """Turn a scalar or length-T list/array into an np.ndarray of length T."""
    if isinstance(x, (int, float)):
        return np.full(T, float(x))
    arr = np.asarray(x, float)
    if arr.shape == (T,):
        return arr
    raise ValueError(f"Expected scalar or length-{T} array, got shape {arr.shape}")

class System:
    """ """

    def __init__(self, components, resources, time_index, builder=None) -> None:
        """ """
        self.components: list[Component] = components
        self.resources: list[Resource] = resources
        self.time_index = time_index
        self.builder = builder if builder else PyomoModelBuilder()
        self.comp_map = {comp.name: comp for comp in components}
        self.res_map = {res.name: res for res in resources}
        self._normalize_time_series()

    def add_component(self, comp) -> Self:
        """ """
        self.components.append(comp)
        return self

    def add_resource(self, res) -> Self:
        """ """
        self.resources.append(res)
        return self

    def build(self) -> pyo.ConcreteModel:
        """ """
        model = self.builder.build_model(self)
        return model

    def solve(self) -> pyo.ConcreteModel:
        """ """
        model = self.builder.build_model(self)
        return self.builder.solve_model(model)

    def _normalize_time_series(self) -> None:
        """ """
        for comp in self.components:
            comp.capacity = _broadcast(comp.capacity, len(self.time_index))

            if comp.capacity_factor is not None:
                comp.capacity_factor = _broadcast(comp.capacity_factor, len(self.time_index))

            if comp.dispatch_flexibility == "fixed":
                comp.minimum = comp.capacity
            elif comp.minimum is not None:
                comp.minimum = _broadcast(comp.minimum, len(self.time_index))
            else:
                comp.minimum = np.zeros(len(self.time_index), dtype=float)

            for cf in comp.cashflows:
                cf.reference_price = _broadcast(cf.reference_price, len(self.time_index))
                cf.reference_driver = _broadcast(cf.reference_driver, len(self.time_index))
                cf.scaling_factor_x = _broadcast(cf.scaling_factor_x, len(self.time_index))
