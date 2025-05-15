# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import Any, Self

import pandas as pd
import pyomo.environ as pyo  # type: ignore[import-untyped]

from dove.models import register_builder
from dove.models.base import BaseModelBuilder

from . import rulelib as prl


@register_builder("price_taker")
class PriceTakerBuilder(BaseModelBuilder):
    """ """

    def build(self) -> Self:
        """ """
        self.model = pyo.ConcreteModel()
        self.model.system = self.system

        self._add_sets()
        self._add_variables()
        self._add_constraints()
        self._add_objective()

        return self

    def solve(self, **kw: Any) -> pyo.ConcreteModel:
        """ """
        solver = pyo.SolverFactory(kw.get("solver", "cbc"))
        solver.solve(self.model)
        return self.model

    def extract_results(self) -> pd.DataFrame:
        """ """
        m = self.model
        data = {}
        T = self.system.time_index
        for comp in self.system.components:
            for res in comp.produces + comp.consumes:
                sign = -1 if res in comp.consumes else 1
                direction = "consumes" if sign == -1 else "produces"
                vals = [pyo.value(m.flow[comp.name, res.name, t]) * sign for t in T]
                data[f"{comp.name}_{res.name}_{direction}"] = vals

            if comp.name in m.STORAGE:
                data[f"{comp.name}_SOC"] = [pyo.value(m.SOC[comp.name, t]) for t in T]
                data[f"{comp.name}_charge"] = [pyo.value(m.charge[comp.name, t]) for t in T]
                data[f"{comp.name}_discharge"] = [pyo.value(m.discharge[comp.name, t]) for t in T]

        return pd.DataFrame(data, index=T)

    def _add_sets(self) -> None:
        """ """
        non_storage_comp_names = self.model.system.non_storage_comp_names
        storage_comp_names = self.model.system.storage_comp_names

        self.model.NON_STORAGE = pyo.Set(initialize=non_storage_comp_names)
        self.model.STORAGE = pyo.Set(initialize=storage_comp_names)
        self.model.R = pyo.Set(initialize=[r.name for r in self.system.resources])
        self.model.T = pyo.Set(initialize=self.system.time_index, ordered=True)

    def _add_variables(self) -> None:
        m = self.model
        m.flow = pyo.Var(m.NON_STORAGE, m.R, m.T, within=pyo.NonNegativeReals)

        # Storage Variables
        m.SOC = pyo.Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)
        m.charge = pyo.Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)
        m.discharge = pyo.Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)

        # # Ramp tracking variables
        # m.ramp_up = Var(m.C, m.T, within=NonNegativeReals)
        # m.ramp_down = Var(m.C, m.T, within=NonNegativeReals)
        # m.ramp_up_bin = Var(m.C, m.T, within=Binary)
        # m.ramp_down_bin = Var(m.C, m.T, within=Binary)

    def _add_constraints(self) -> None:
        m = self.model

        m.transfer = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.transfer_rule)
        m.capacity = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.capacity_rule)
        m.min_capacity = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.min_rule)
        m.fixed_profile = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.fixed_profile_rule)

        m.resource_balance = pyo.Constraint(m.R, m.T, rule=prl.balance_rule)

        # Storage Constraints
        m.storage_balance = pyo.Constraint(m.STORAGE, m.T, rule=prl.storage_balance_rule)
        m.charge_limit = pyo.Constraint(m.STORAGE, m.T, rule=prl.charge_limit_rule)
        m.discharge_limit = pyo.Constraint(m.STORAGE, m.T, rule=prl.discharge_limit_rule)
        m.soc_limit = pyo.Constraint(m.STORAGE, m.T, rule=prl.soc_limit_rule)

        # # Ramp Constraints
        # def ramp_rule(m, cname, t):
        #     comp = system.comp_map[cname]
        #     if comp.ramp_limit is None or t == m.T.first():
        #         return pyo.Constraint.Skip
        #     res = comp.capacity_resource.name
        #     flow_diff = m.flow[cname, res, t] - m.flow[cname, res, m.T.prev(t)]
        #     yield flow_diff <= comp.ramp_limit
        #     yield -flow_diff <= comp.ramp_limit
        # m.ramp_limit = Constraint(m.C, m.T, rule=ramp_rule)

        # # Ramp Frequency Constraints
        # def ramp_freq_rule(m, cname, t):
        #     comp = system.comp_map[cname]
        #     if comp.ramp_freq is None or t == m.T.first():
        #         return pyo.Constraint.Skip
        #     yield m.ramp_up[cname, t] >= m.flow[cname, comp.capacity_resource.name, t] - m.flow[cname, comp.capacity_resource.name, m.T.prev(t)]
        #     yield m.ramp_down[cname, t] >= m.flow[cname, comp.capacity_resource.name, m.T.prev(t)] - m.flow[cname, comp.capacity_resource.name, t]
        #     yield m.ramp_up[cname, t] <= comp.max_capacity * m.ramp_up_bin[cname, t]
        #     yield m.ramp_down[cname, t] <= comp.max_capacity * m.ramp_down_bin[cname, t]
        #     yield m.ramp_up_bin[cname, t] + m.ramp_down_bin[cname, t] <= 1
        #     freq_window = [t2 for t2 in m.T if m.T.ord(t2) >= m.T.ord(t)-comp.ramp_freq+1 and m.T.ord(t2) <= m.T.ord(t)]
        #     yield sum(m.ramp_up_bin[cname, tw] + m.ramp_down_bin[cname, tw] for tw in freq_window) <= comp.ramp_freq
        # m.ramp_freq = Constraint(m.C, m.T, rule=ramp_freq_rule)

    def _add_objective(self) -> None:
        self.model.objective = pyo.Objective(rule=prl.objective_rule, sense=pyo.maximize)
