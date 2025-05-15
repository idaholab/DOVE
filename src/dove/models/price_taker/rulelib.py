# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import TYPE_CHECKING

import pyomo.environ as pyo  # type: ignore

if TYPE_CHECKING:
    from dove.core import Storage


# Transfer Constraints (Converters)
def transfer_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Expression:
    """ """
    comp = m.system.comp_map[cname]
    inputs = {r.name: m.flow[cname, r.name, t] for r in comp.consumes}
    outputs = {r.name: m.flow[cname, r.name, t] for r in comp.produces}
    return comp.transfer_fn(inputs, outputs)


def capacity_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Expression:
    """ """
    comp = m.system.comp_map[cname]
    return m.flow[cname, comp.capacity_resource.name, t] <= comp.max_capacity


def min_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Expression:
    """ """
    comp = m.system.comp_map[cname]
    return m.flow[cname, comp.capacity_resource.name, t] >= comp.min_capacity


def fixed_profile_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Expression:
    """ """
    comp = m.system.comp_map[cname]
    if len(comp.profile) == 0:
        return pyo.Constraint.Skip
    return m.flow[cname, comp.capacity_resource.name, t] == comp.profile[t]


# Resource Balance Constraints
def balance_rule(m: pyo.ConcreteModel, rname: str, t: int) -> pyo.Expression:
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


def storage_balance_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """ """
    comp = m.system.comp_map[sname]
    if t == m.T.first():
        soc_prev = comp.initial_stored * comp.max_capacity
    else:
        soc_prev = m.SOC[sname, m.T.prev(t)]
    return m.SOC[sname, t] == soc_prev + (
        m.charge[sname, t] * comp.rte**0.5 - m.discharge[sname, t] / comp.rte**0.5
    )


def charge_limit_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """ """
    comp: Storage = m.system.comp_map[sname]
    return m.charge[sname, t] <= comp.max_charge_rate * comp.max_capacity


def discharge_limit_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """"""
    comp: Storage = m.system.comp_map[sname]
    return m.discharge[sname, t] <= comp.max_discharge_rate * comp.max_capacity


def soc_limit_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """ """
    comp: Storage = m.system.comp_map[sname]
    return m.SOC[sname, t] <= comp.max_capacity


def objective_rule(m: pyo.ConcreteModel) -> pyo.Expression:
    """ """
    total = 0
    for comp in m.system.components:
        # TODO: cashflow defaults to capacity_resource
        # we should find a way to do different resource vars like level/charge/discharge
        rname = comp.capacity_resource.name
        for cf in comp.cashflows:
            for t in m.T:
                dispatch = m.flow[comp.name, rname, t]
                total += cf.sign * cf.price_profile[t] * ((dispatch / cf.dprime) ** cf.scalex)
    return total
