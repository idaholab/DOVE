# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from math import sqrt

from pyomo.environ import Constraint


def cap_rule(m, cname, t):
    """ """
    return m.dispatch[cname, t] <= m.capacity[cname, t]


def min_rule(m, cname, t):
    """ """
    return m.dispatch[cname, t] >= m.minimum[cname, t]


def charge_limit(m, comp_name, t):
    """ """
    max_charge = m.system.comp_map[comp_name].max_charge_rate
    return m.charge[comp_name, t] <= max_charge


def discharge_limit(m, cname, t):
    """ """
    max_discharge = m.system.comp_map[cname].max_discharge_rate
    return m.discharge[cname, t] <= max_discharge


def soc_balance(m, cname, t):
    """ """
    comp = m.system.comp_map[cname]
    sqrt_rte = sqrt(comp.rte)
    if t == m.system.time_index[0]:
        prev = comp.initial_stored
    else:
        prev_t = m.system.time_index[t - 1]
        prev = m.soc[cname, prev_t]
    return (
        m.soc[cname, t]
        == prev + sqrt_rte * m.charge[cname, t] - m.discharge[cname, t] / sqrt_rte
    )


def flow_rule(m, rname, t):
    """ """
    resource = m.system.res_map[rname]
    expr = None
    for cname in m.NON_STORAGE:
        comp = m.system.comp_map[cname]
        for term in comp.transfer_terms:
            exp = term.exponent.get(resource, 0)
            if exp != 0:
                term_expr = term.coeff * (m.dispatch[cname, t] ** exp)
                if expr is None:
                    expr = term_expr
                else:
                    expr += term_expr
    for stor_cname in m.STORAGE:
        # TODO: Hardcoding storage transfer terms is not great...
        expr += -1.0 * (m.charge[stor_cname, t] ** 1)
        expr += +1.0 * (m.discharge[stor_cname, t] ** 1)

    if expr is None:
        expr = Constraint.Skip

    return expr == 0.0
