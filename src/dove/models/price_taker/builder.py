# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import Self

import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import ConcreteModel, Constraint, Objective, Set, Var, value

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
        self._add_variables()
        self._add_constraints()
        self._add_objective()

        return self

    def solve(self, **kw):
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
                vals = [value(m.flow[comp.name, res.name, t]) * sign for t in T]
                data[f"{comp.name}_{res.name}_{direction}"] = vals

            if comp.name in m.STORAGE:
                data[f"{comp.name}_SOC"] = [value(m.SOC[comp.name, t]) for t in T]
                data[f"{comp.name}_charge"] = [value(m.charge[comp.name, t]) for t in T]
                data[f"{comp.name}_discharge"] = [value(m.discharge[comp.name, t]) for t in T]

        return pd.DataFrame(data, index=T)

    def _add_sets(self):
        """ """
        non_storage_comp_names = self.model.system.non_storage_comp_names
        storage_comp_names = self.model.system.storage_comp_names

        self.model.NON_STORAGE = Set(initialize=non_storage_comp_names)
        self.model.STORAGE = Set(initialize=storage_comp_names)
        self.model.R = Set(initialize=[r.name for r in self.system.resources])
        self.model.T = Set(initialize=self.system.time_index, ordered=True)

    def _add_variables(self):
        m = self.model
        m.flow = Var(m.NON_STORAGE, m.R, m.T, within=pyo.NonNegativeReals)

        # Storage Variables
        m.SOC = Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)
        m.charge = Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)
        m.discharge = Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)

        # # Ramp tracking variables
        # m.ramp_up = Var(m.C, m.T, within=NonNegativeReals)
        # m.ramp_down = Var(m.C, m.T, within=NonNegativeReals)
        # m.ramp_up_bin = Var(m.C, m.T, within=Binary)
        # m.ramp_down_bin = Var(m.C, m.T, within=Binary)

    def _add_constraints(self):
        m, system = self.model, self.system

        m.transfer = Constraint(m.NON_STORAGE, m.T, rule=prl.transfer_rule)
        m.capacity = Constraint(m.NON_STORAGE, m.T, rule=prl.capacity_rule)
        m.min_capacity = Constraint(m.NON_STORAGE, m.T, rule=prl.min_rule)
        m.fixed_profile = Constraint(m.NON_STORAGE, m.T, rule=prl.fixed_profile_rule)

        m.resource_balance = Constraint(m.R, m.T, rule=prl.balance_rule)

        # Storage Constraints
        m.storage_balance = Constraint(m.STORAGE, m.T, rule=prl.storage_balance_rule)

        m.charge_limit = Constraint(
            m.STORAGE, m.T,
            rule=lambda m, s, t: m.charge[s, t] <= system.comp_map[s].max_charge_rate * system.comp_map[s].max_capacity
        )

        m.discharge_limit = Constraint(
            m.STORAGE, m.T,
            rule=lambda m, s, t: m.discharge[s, t] <= system.comp_map[s].max_discharge_rate * system.comp_map[s].max_capacity
        )
        m.soc_limit = Constraint(
            m.STORAGE, m.T,
            rule=lambda m, s, t: m.SOC[s, t] <= system.comp_map[s].max_capacity
        )

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

    def _add_objective(self):
        m, system = self.model, self.system
        def objective_rule(m):
            total = 0
            for comp in system.components:
                # TODO: cashflow defaults to capacity_resource we should find a way to do different tracking vars
                rname = comp.capacity_resource.name
                for cf in comp.cashflows:
                    for t in m.T:
                        dispatch = m.flow[comp.name, rname, t]
                        total += cf.sign * cf.price_profile[t] * ((dispatch / cf.dprime) ** cf.scalex)
            return total
        m.objective = Objective(rule=objective_rule, sense=pyo.maximize)
