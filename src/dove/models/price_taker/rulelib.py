# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from math import sqrt

from pyomo.environ import Constraint, Expression


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


def flow_rule(m, res_name, t):
    net = 0
    system = m.system

    for cname in system.non_storage_comp_names:
        comp = system.comp_map[cname]
        dispatch = m.dispatch[cname, t]

        # Transfer function explicitly ONLY uses the single dispatch variable
        inputs = {comp.capacity_resource.name: dispatch}

        # Evaluate transfer_fn using ONLY the dispatch var
        out_map = comp.transfer_fn(**inputs)

        for rsrc, expr in out_map.items():
            if rsrc in comp.produces:
                net += expr
            if rsrc in comp.consumes:
                net -= expr

    # Storage components (if any)
    for stor_name in system.storage_comp_names:
        net += m.discharge[stor_name, t] - m.charge[stor_name, t]

    return net == 0
