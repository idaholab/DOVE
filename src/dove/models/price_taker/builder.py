# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import Self

import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import (
    ConcreteModel,
    Constraint,
    Objective,
    Param,
    Set,
    Var,
    value,
)

from .. import register_builder
from ..base import BaseModelBuilder
from . import rulelib as prl


@register_builder("price_taker")
class PriceTakerBuilder(BaseModelBuilder):
    """ """

    def build(self) -> Self:
        """ """
        self.model = ConcreteModel()
        self.model.system = self.system
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
            if comp_name in self.system.storage_comp_names:
                col_charge = f"{comp_name}_{comp.resource.name}_charge"
                vals_charge = []
                col_discharge = f"{comp_name}_{comp.resource.name}_discharge"
                vals_discharge = []
                col_soc = f"{comp_name}_soc_level"
                vals_soc = []
                for t in self.system.time_index:
                    soc = value(self.model.soc[comp_name, t], exception=True)
                    chg = value(self.model.charge[comp_name, t], exception=True)
                    dchg = value(self.model.discharge[comp_name, t], exception=True)
                    vals_charge.append(-1.0 * (chg ** 1))
                    vals_discharge.append(+1.0 * (dchg ** 1))
                    vals_soc.append(soc)
                data[col_charge] = vals_charge
                data[col_discharge] = vals_discharge
                data[col_soc] = vals_soc

            for term in comp.transfer_terms:
                for res, exp in term.exponent.items():
                    if exp == 0:
                        continue
                    direction = "production" if term.coeff > 0 else "consumption"
                    col = f"{comp_name}_{res.name}_{direction}"
                    vals = []
                    for t in self.system.time_index:
                        d = value(self.model.dispatch[comp_name, t], exception=True)
                        assert d is not None
                        vals.append(term.coeff * (d ** exp))
                    data[col] = vals
            for cf in comp.cashflows:
                if len(cf.price_profile) > 0:
                    data[f"{cf.name}_signal"] = cf.price_profile
        df = pd.DataFrame(data, index=self.system.time_index)
        return df


    def _add_sets(self) -> None:
        comp_names = list(self.system.comp_map.keys())
        res_names = list(self.system.res_map.keys())
        times = self.system.time_index

        self.model.COMPS = Set(initialize=comp_names, ordered=True)
        self.model.RESOURCES = Set(initialize=res_names, ordered=True)
        self.model.TIMES = Set(initialize=times, ordered=True)

        non_storage_names = self.system.non_storage_comp_names
        self.model.NON_STORAGE = Set(initialize=non_storage_names, ordered=True)

        storage_names = self.system.storage_comp_names
        self.model.STORAGE = Set(initialize=storage_names, ordered=True)

    def _add_params(self) -> None:
        """ """
        def _cap_init(m, comp_name, t):
            comp = m.system.comp_map[comp_name]
            return comp.max_capacity

        self.model.capacity = Param(self.model.COMPS, self.model.TIMES, initialize=_cap_init, mutable=False)

        def _min_init(m, comp_name, t):
            comp = m.system.comp_map[comp_name]
            return comp.min_capacity

        self.model.minimum = Param(self.model.COMPS, self.model.TIMES, initialize=_min_init, mutable=False)


    def _add_vars(self) -> None:
        """ """
        self.model.dispatch = Var(self.model.NON_STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)
        self.model.charge = Var(self.model.STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)
        self.model.discharge = Var(self.model.STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)
        self.model.soc = Var(self.model.STORAGE, self.model.TIMES, within=pyo.NonNegativeReals)

    def _add_constraints(self):
        self.model.CapacityConstraint = Constraint(self.model.NON_STORAGE, self.model.TIMES, rule=prl.cap_rule)
        self.model.MinimumConstraint = Constraint(self.model.NON_STORAGE, self.model.TIMES, rule=prl.min_rule)
        self.model.ChargeLimit = Constraint(self.model.STORAGE, self.model.TIMES, rule=prl.charge_limit)
        self.model.DischargeLimit = Constraint(self.model.STORAGE, self.model.TIMES, rule=prl.discharge_limit)
        self.model.SOCBalance = Constraint(self.model.STORAGE, self.model.TIMES, rule=prl.soc_balance)
        self.model.FlowConstraint = Constraint(self.model.RESOURCES, self.model.TIMES, rule=prl.flow_rule)


    def _add_objective(self) -> None:
        expr = 0.0
        for comp in self.system.components:
            for cf in comp.cashflows:
                for t in self.model.TIMES:
                    expr += cf.sign * cf.price_profile[t] * (self.model.dispatch[comp.name, t] / cf.dprime) ** cf.scalex

        self.model.Objective = Objective(expr=expr, sense=pyo.maximize)

