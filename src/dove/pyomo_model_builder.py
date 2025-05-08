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

        m = pyo.ConcreteModel()

        self._add_sets(m, system)

        self._add_params(m, system)

        self._add_vars(m, system)

        self._add_constraints(m, system)

        self._add_objective(m, system)

        return cast(pyo.ConcreteModel, m)

    def solve_model(self, model) -> pyo.ConcreteModel:
        """ """
        opt = pyo.SolverFactory("cbc")
        opt.solve(model, tee=True, keepfiles=False)
        return model


    def _add_sets(self, m, system):
        m.COMPS = pyo.Set(initialize=list(system.comp_map.keys()), ordered=True)
        m.RESOURCES = pyo.Set(initialize=list(system.res_map.keys()), ordered=True)
        m.TIMES = pyo.Set(initialize=system.time_index, ordered=True)

    def _add_params(self, m, system):
        def _cap_init(m, comp_name, t):
            comp = system.comp_map[comp_name]
            return comp.capacity[t]
        m.capacity = pyo.Param(m.COMPS, m.TIMES, initialize=_cap_init, mutable=False)

        def _min_init(m, comp_name, t):
            comp = system.comp_map[comp_name]
            return comp.minimum[t]
        m.minimum = pyo.Param(m.COMPS, m.TIMES, initialize=_min_init, mutable=False)


    def _add_vars(self, m, system):
        m.dispatch = pyo.Var(m.COMPS, m.TIMES, within=pyo.NonNegativeReals)


    def _add_constraints(self, m, system):
        def _cap_rule(m, comp_name, t):
            return m.dispatch[comp_name, t] <= m.capacity[comp_name, t]

        m.CapacityConstraint = pyo.Constraint(m.COMPS, m.TIMES, rule=_cap_rule)

        def _min_rule(m, comp_name, t):
            return m.dispatch[comp_name, t] >= m.minimum[comp_name, t]
        m.MinimumConstraint = pyo.Constraint(m.COMPS, m.TIMES, rule=_min_rule)

        def _flow_rule(m, res_name, t):
            resource = system.res_map[res_name]
            expr = None
            for comp_name in m.COMPS:
                comp = system.comp_map[comp_name]
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

        m.FlowConstraint = pyo.Constraint(m.RESOURCES, m.TIMES, rule=_flow_rule)


    def _add_objective(self, m, system):
        expr = 0.0
        for comp in system.components:
            for cf in comp.cashflows:
                for t in m.TIMES:
                    expr += cf.sign * cf.reference_price[t] * (m.dispatch[comp.name, t] / cf.reference_driver[t]) ** cf.scaling_factor_x[t]

        m.Objective = pyo.Objective(expr=expr, sense=pyo.maximize)

