# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import ConcreteModel, Set, Var, Constraint, Objective, value, NonNegativeReals, Binary
from .. import register_builder
from ..base import BaseModelBuilder

@register_builder("price_taker")
class PriceTakerBuilder(BaseModelBuilder):

    def build(self):
        self.model = ConcreteModel()
        self.model.system = self.system

        self._add_sets()
        self._add_variables()
        self._add_constraints()
        self._add_objective()

        return self

    def solve(self):
        solver = pyo.SolverFactory("cbc")
        solver.solve(self.model)
        return self.model

    def extract_results(self) -> pd.DataFrame:
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
        m = self.model
        m.NON_STORAGE = Set(initialize=[cname for cname in m.system.non_storage_comp_names])
        m.STORAGE = Set(initialize=[cname for cname in m.system.storage_comp_names])
        m.R = Set(initialize=[r.name for r in self.system.resources])
        m.T = Set(initialize=self.system.time_index, ordered=True)

    def _add_variables(self):
        m = self.model
        m.flow = Var(m.NON_STORAGE, m.R, m.T, within=NonNegativeReals)

        # Storage Variables
        m.SOC = Var(m.STORAGE, m.T, within=NonNegativeReals)
        m.charge = Var(m.STORAGE, m.T, within=NonNegativeReals)
        m.discharge = Var(m.STORAGE, m.T, within=NonNegativeReals)

        # # Ramp tracking variables
        # m.ramp_up = Var(m.C, m.T, within=NonNegativeReals)
        # m.ramp_down = Var(m.C, m.T, within=NonNegativeReals)
        # m.ramp_up_bin = Var(m.C, m.T, within=Binary)
        # m.ramp_down_bin = Var(m.C, m.T, within=Binary)

    def _add_constraints(self):
        m, system = self.model, self.system

        # Transfer Constraints (Converters)
        def transfer_rule(m, cname, t):
            comp = m.system.comp_map[cname]
            inputs = {r.name: m.flow[cname, r.name, t] for r in comp.consumes}
            outputs = {r.name: m.flow[cname, r.name, t] for r in comp.produces}
            return comp.transfer_fn(inputs, outputs)
        m.transfer = Constraint(m.NON_STORAGE, m.T, rule=transfer_rule)

        # Capacity Constraints
        def capacity_rule(m, cname, t):
            comp = system.comp_map[cname]
            return m.flow[cname, comp.capacity_resource.name, t] <= comp.max_capacity
        m.capacity = Constraint(m.NON_STORAGE, m.T, rule=capacity_rule)

        def min_rule(m, cname, t):
            comp = m.system.comp_map[cname]
            return m.flow[cname, comp.capacity_resource.name, t] >= comp.min_capacity
        m.min_capacity = Constraint(m.NON_STORAGE, m.T, rule=min_rule)

        # Resource Balance Constraints
        def balance_rule(m, rname, t):
            prod = sum(m.flow[c.name, rname, t]
                       for c in system.components
                       if rname in c.produces_by_name)

            cons = sum(m.flow[c.name, rname, t]
                       for c in system.components
                       if rname in c.consumes_by_name)

            storage_change = sum(
                m.discharge[s, t] - m.charge[s, t]
                for s in m.STORAGE
                if system.comp_map[s].resource.name == rname
            )
            return prod - cons + storage_change == 0
        m.resource_balance = Constraint(m.R, m.T, rule=balance_rule)

        # Storage Constraints
        def storage_balance_rule(m, sname, t):
            comp = system.comp_map[sname]
            if t == m.T.first():
                soc_prev = comp.initial_stored * comp.max_capacity
            else:
                soc_prev = m.SOC[sname, m.T.prev(t)]
            return m.SOC[sname, t] == soc_prev + \
                (m.charge[sname, t] * comp.rte**0.5 - m.discharge[sname, t] / comp.rte**0.5)
        m.storage_balance = Constraint(m.STORAGE, m.T, rule=storage_balance_rule)

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
                rname = comp.capacity_resource.name
                for cf in comp.cashflows:
                    for t in m.T:
                        dispatch = m.flow[comp.name, rname, t]
                        total += cf.sign * cf.price_profile[t] * ((dispatch / cf.dprime) ** cf.scalex)
            return total
        m.objective = Objective(rule=objective_rule, sense=pyo.maximize)
