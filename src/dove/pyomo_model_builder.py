# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import cast
import pyomo.environ as pyo


class PyomoModelBuilder:
    """ """

    def __init__(self) -> None:
        """ """
        pass

    def build_model(self, system) -> pyo.ConcreteModel:
        """ """

        self._normalize_time_series(system)

        m = pyo.ConcreteModel()

        self._add_sets(m, system)

        self._add_vars(m, system)

        self._add_constraints(m, system)

        self._add_objective(m, system)

        return cast(pyo.ConcreteModel, m)

    def solve_model(self, model):
        """ """
        pass

    def _normalize_time_series(self, system):
        pass

    def _add_sets(self, m, system):
        pass

    def _add_vars(self, m, system):
        pass

    def _add_constraints(self, m, system):
        pass

    def _add_objective(self, m, system):
        pass
