# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import Self

import pandas as pd
import pyomo.environ as pyo
from pyomo.solvers.tests.solvers import initialize

from .. import register_builder
from ..base import BaseModelBuilder


@register_builder("price_taker")
class PriceTakerBuilder(BaseModelBuilder):
    """ """

    def build(self) -> Self:
        """ """
        self.model = pyo.ConcreteModel()
        self._add_sets()
        self._add_params()
        self._add_vars()
        self._add_constraints()
        self._add_objective()
        return self

    def solve(self):
        """ """
        opt = pyo.SolverFactory("cbc")
        opt.solve(self.model)
        return self.model

    def extract_results(self) -> pd.DataFrame:
        """ """
        data: dict[str, list[float]] = {}
        for comp_name, comp in self.system.comp_map.items():
            for term in comp.transfer_terms:
                for res, exp in term.exponent.items():
                    if exp == 0:
                        continue
                    direction = "production" if term.coeff > 0 else "consumption"
                    col = f"{comp_name}_{res.name}_{direction}"
                    vals = []
                    for t in self.system.time_index:
                        d = pyo.value(self.model.dispatch[comp_name, t], exception=True)
                        assert d is not None
                        vals.append(term.coeff * (d ** exp))
                    data[col] = vals
        df = pd.DataFrame(data, index=self.system.time_index)
        return df


    def _add_sets(self) -> None:
        comp_names = list(self.system.comp_map.keys())
        res_names = list(self.system.res_map.keys())
        times = self.system.time_index

        non_storage_names = self.system.non_storage_comp_names
        self.model.NON_STORAGE = pyo.Set(initialize=non_storage_names, ordered=True)
        self.model.RESOURCES = pyo.Set(initialize=res_names, ordered=True)
        self.model.TIMES = pyo.Set(initialize=times, ordered=True)

        storage_names = self.system.storage_comp_names
        self.model.STORAGE = pyo.Set(initialize=storage_names, ordered=True)

    def _add_params(self) -> None:
        """ """
        def _cap_init(m, comp_name, t):
            comp = self.system.comp_map[comp_name]
            return comp.max_capacity

        self.model.capacity = pyo.Param(
            self.model.NON_STORAGE, self.model.TIMES, initialize=_cap_init, mutable=False
        )

        def _min_init(m, comp_name, t):
            comp = self.system.comp_map[comp_name]
            return comp.min_capacity

        self.model.minimum = pyo.Param(
            self.model.NON_STORAGE, self.model.TIMES, initialize=_min_init, mutable=False
        )


    def _add_vars(self) -> None:
        """ """
        self.model.dispatch = pyo.Var(
            self.model.NON_STORAGE, self.model.TIMES, within=pyo.NonNegativeReals
        )

        self.model.charge = pyo.Var(self.model.STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)
        self.model.discharge = pyo.Var(self.model.STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)
        self.model.soc = pyo.Var(self.model.STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)

    def _add_constraints(self):
        def _cap_rule(m, comp_name, t):
            return m.dispatch[comp_name, t] <= m.capacity[comp_name, t]

        self.model.CapacityConstraint = pyo.Constraint(self.model.NON_STORAGE, self.model.TIMES, rule=_cap_rule)

        def _min_rule(m, comp_name, t):
            return m.dispatch[comp_name, t] >= m.minimum[comp_name, t]
        self.model.MinimumConstraint = pyo.Constraint(self.model.NON_STORAGE, self.model.TIMES, rule=_min_rule)

        def _charge_limit(m, comp_name, t):
            max_charge = self.system.comp_map[comp_name].max_charge_rate
            return self.model.charge[comp_name, t] <= max_charge
        self.model.ChargeLimit = pyo.Constraint(self.model.STORAGE, self.model.TIMES, rule=_charge_limit)
        
        def _discharge_limit(m, comp_name, t):
            max_discharge = self.system.comp_map[comp_name].max_discharge_rate
            return self.model.discharge[comp_name, t] <= max_discharge
        self.model.DischargeLimit = pyo.Constraint(self.model.STORAGE, self.model.TIMES, rule=_discharge_limit)

        def _flow_rule(m, res_name, t):
            resource = self.system.res_map[res_name]
            expr = None
            for comp_name in m.COMPS:
                comp = self.system.comp_map[comp_name]
                for term in comp.transfer_terms:
                    exp = term.exponent.get(resource, 0)
                    if exp != 0:
                        term_expr = term.coeff * (m.dispatch[comp_name, t] ** exp)
                        if expr is None:
                            expr = term_expr
                        else:
                            expr += term_expr
            if expr is None:
                expr = pyo.Constraint.Skip

            return expr == 0.0

        self.model.FlowConstraint = pyo.Constraint(self.model.RESOURCES, self.model.TIMES, rule=_flow_rule)


    def _add_objective(self) -> None:
        expr = 0.0
        for comp in self.system.components:
            for cf in comp.cashflows:
                for t in self.model.TIMES:
                    expr += cf.sign * cf.price_profile[t] * (self.model.dispatch[comp.name, t] / cf.dprime) ** cf.scalex

        self.model.Objective = pyo.Objective(expr=expr, sense=pyo.maximize)

