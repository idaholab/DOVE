# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from pyomo.environ import Constraint


# Transfer Constraints (Converters)
def transfer_rule(m, cname, t):
    """ """
    comp = m.system.comp_map[cname]
    inputs = {r.name: m.flow[cname, r.name, t] for r in comp.consumes}
    outputs = {r.name: m.flow[cname, r.name, t] for r in comp.produces}
    return comp.transfer_fn(inputs, outputs)


def capacity_rule(m, cname, t):
    """ """
    comp = m.system.comp_map[cname]
    return m.flow[cname, comp.capacity_resource.name, t] <= comp.max_capacity


def min_rule(m, cname, t):
    """ """
    comp = m.system.comp_map[cname]
    return m.flow[cname, comp.capacity_resource.name, t] >= comp.min_capacity


def fixed_profile_rule(m, cname, t):
    """ """
    comp = m.system.comp_map[cname]
    if len(comp.profile) == 0:
        return Constraint.Skip
    return m.flow[cname, comp.capacity_resource.name, t] == comp.profile[t]


# Resource Balance Constraints
def balance_rule(m, rname, t):
    """ """
    prod = sum(
        m.flow[cname, rname, t]
        for cname in m.NON_STORAGE
        if rname in m.system.comp_map[cname].produces_by_name
    )

    cons = sum(
        m.flow[cname, rname, t]
        for cname in m.NON_STORAGE
        if rname in m.system.comp_map[cname].consumes_by_name
    )

    storage_change = sum(
        m.discharge[s, t] - m.charge[s, t]
        for s in m.STORAGE
        if m.system.comp_map[s].resource.name == rname
    )
    return prod - cons + storage_change == 0


def storage_balance_rule(m, sname, t):
    """ """
    comp = m.system.comp_map[sname]
    if t == m.T.first():
        soc_prev = comp.initial_stored * comp.max_capacity
    else:
        soc_prev = m.SOC[sname, m.T.prev(t)]
    return m.SOC[sname, t] == soc_prev + (
        m.charge[sname, t] * comp.rte**0.5 - m.discharge[sname, t] / comp.rte**0.5
    )
