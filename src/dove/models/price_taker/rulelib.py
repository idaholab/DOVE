# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.models.price_taker.rulelib``
====================================

Rule functions for price-taker pyomo optimization models.

This module provides a collection of rules that can be used to define constraints
and objectives in price-taker optimization models using the Pyomo framework. The rules
define mathematical relationships that govern how components interact within an energy
system, including resource transfers, capacity limitations, and storage dynamics.

The module includes functions for:
- Component transfer constraints (input/output relationships)
- Capacity constraints (min/max capacity limits)
- Resource balance constraints (ensuring conservation)
- Storage-specific constraints (charge/discharge rates, state of charge)
- Objective function formulation for economic optimization

These rules are designed to be used with Pyomo's rule-based constraint and objective
declaration syntax. Each function returns a Pyomo expression that defines the
mathematical relationship for the respective constraint or objective.

All rule functions assume the existence of a PyomoConcreteModel with appropriate
variables, parameters, and sets already defined. The model is expected to have
a 'system' attribute containing component and resource information.
"""

from typing import TYPE_CHECKING

import numpy as np
import pyomo.environ as pyo  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from dove.core import Storage


def transfer_block_rule(b: pyo.Block, cname: str, t: int) -> None:
    """
    Sets up a block that handles resource transfer for components.

    The function creates a Pyomo Block that is specific to a non-storage component. It finds the
    flow information for this component at the given timestep and provides this data to the
    component's transfer function, which returns a list of values. This function creates a variable
    on the block called transfer_size. A constraint is also created on the block that forces each
    value in the list from the transfer function to equal the transfer_size. Effectively, every
    value in the list from the transfer function is forced to be equal, which establishes the
    desired relationship between the inputs and outputs for the component.

    Parameters
    ----------
    b : pyo.Block
        The Pyomo block to populate with transfer information and constraints.
    cname : str
        The name of the component for which the transfer block is being defined.
    t : int
        The time step for which the block applies.

    Returns
    -------
    None

    Notes
    -----
    This function assumes that the component has a defined capacity_resource attribute, a
    time-dependent max_capacity_profile, and an appropriate transfer_fn. These should already
    have been validated.
    """
    # Get the model's current behavior (flows)
    m = b.model()
    comp = m.system.comp_map[cname]
    input_res_quantities = {r.name: m.flow[cname, r.name, t] for r in comp.consumes}
    output_res_quantities = {r.name: m.flow[cname, r.name, t] for r in comp.produces}

    # Apply transfer function to get list of values that should be equal
    tf_values = comp.transfer_fn(input_res_quantities, output_res_quantities)

    MIN_VALUES = 2
    if len(tf_values) >= MIN_VALUES:  # If resource transfer is applicable
        # Create necessary variable
        b.transfer_size = pyo.Var(within=pyo.NonNegativeReals)

        # Create constraint to force equality of all returned values
        def transfer_rule(b: pyo.Block, i: int) -> pyo.Expression:
            return tf_values[i] == b.transfer_size

        b.transfer_constr = pyo.Constraint(range(len(tf_values)), rule=transfer_rule)


def max_capacity_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Expression:
    """
    Creates a constraint rule for limiting resource flow up to component's max capacity at the given timestep.

    The function creates a Pyomo rule expression that constrains the flow of the
    capacity resource for a given component at a specific time period to be less than
    or equal to the maximum capacity of that component at the given timestep.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The Pyomo model containing the system components and variables.
    cname : str
        The name of the component for which the max capacity constraint is being defined.
    t : int
        The time step for which the constraint applies.

    Returns
    -------
    pyo.Expression
        A Pyomo expression representing the capacity constraint for the given component
        at the specified time period.

    Notes
    -----
    This function assumes that the component has a defined capacity_resource attribute
    and a time-dependent max_capacity_profile. These values should already been validated.
    """
    comp = m.system.comp_map[cname]
    return m.flow[cname, comp.capacity_resource.name, t] <= comp.max_capacity_profile[t]


def min_capacity_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Expression:
    """
    Generate a constraint that enforces minimum capacity for a component at a given timestep.

    This function creates a pyomo expression that constrains the flow of a
    component to be greater than or equal to its minimum capacity at the given timestep.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The pyomo model to which the constraint will be added.
    cname : str
        The name of the component.
    t : int
        The time step for which the constraint applies.

    Returns
    -------
    pyo.Expression
        A pyomo expression representing the minimum capacity constraint.

    Notes:
    Assumes that min_capacity_profile is a time-dependent attribute of the component.
    """
    comp = m.system.comp_map[cname]
    return m.flow[cname, comp.capacity_resource.name, t] >= comp.min_capacity_profile[t]


def ramp_up_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Limit rate of increase in component output between time periods.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint limiting upward ramping or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_limit") or t == m.T.first():
        return pyo.Constraint.Skip
    res = comp.capacity_resource.name
    max_allowed_ramp = comp.ramp_limit * np.max(comp.max_capacity_profile)
    return m.flow[cname, res, t] - m.flow[cname, res, m.T.prev(t)] <= max_allowed_ramp


def ramp_down_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Limit rate of decrease in component output between time periods.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint limiting downward ramping or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_limit") or t == m.T.first():
        return pyo.Constraint.Skip
    res = comp.capacity_resource.name
    max_allowed_ramp = comp.ramp_limit * np.max(comp.max_capacity_profile)
    return m.flow[cname, res, m.T.prev(t)] - m.flow[cname, res, t] <= max_allowed_ramp


def ramp_track_up_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Track upward ramps for a component.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint tracking upward ramps or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip
    res = comp.capacity_resource.name
    return m.ramp_up[cname, t] >= m.flow[cname, res, t] - m.flow[cname, res, m.T.prev(t)]


def ramp_track_down_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Track downward ramps for a component.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint tracking downward ramps or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip
    res = comp.capacity_resource.name
    return m.ramp_down[cname, t] >= m.flow[cname, res, m.T.prev(t)] - m.flow[cname, res, t]


def ramp_bin_up_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Limit upward ramp size based on binary variable.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint limiting ramp size or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip
    return m.ramp_up[cname, t] <= comp.max_capacity_profile[t] * m.ramp_up_bin[cname, t]


def ramp_bin_down_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Limit downward ramp size based on binary variable.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint limiting ramp size or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip
    return m.ramp_down[cname, t] <= comp.max_capacity_profile[t] * m.ramp_down_bin[cname, t]


def ramp_freq_window_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Limit frequency of ramping events within a time window.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Constraint limiting ramp frequency or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip

    # Create window of time periods to check for ramping events
    t_ord = m.T.ord(t)
    window_start_ord = max(1, t_ord - comp.ramp_freq + 1)
    freq_window = [t2 for t2 in m.T if window_start_ord <= m.T.ord(t2) <= t_ord]

    return sum(m.ramp_up_bin[cname, tw] + m.ramp_down_bin[cname, tw] for tw in freq_window) <= 1


def steady_state_upper_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Define upper bound for steady state operation (no flow increase if in steady state).

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Upper bound constraint for steady state or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip

    # If steady_bin is 1, then flow difference must be <= 0
    M = 2 * comp.max_capacity_profile[t]
    return m.ramp_up[cname, t] <= M * (1 - m.steady_bin[cname, t])


def steady_state_lower_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Define lower bound for steady state operation (no flow decrease if in steady state).

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Lower bound constraint for steady state or Constraint.Skip
    """
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0 or t == m.T.first():
        return pyo.Constraint.Skip

    # If steady_bin is 1, then flow difference must be >= 0
    M = 2 * comp.max_capacity_profile[t]
    return m.ramp_down[cname, t] >= -M * (1 - m.steady_bin[cname, t])


def state_selection_rule(m: pyo.ConcreteModel, cname: str, t: int) -> pyo.Constraint:
    """
    Ensure exactly one operational state is active at each time step.

    Parameters
    ----------
    m : pyo.ConcreteModel
        Pyomo model
    cname : str
        Component name
    t : int
        Time period

    Returns
    -------
    pyo.Constraint
        Component must be in exactly one state (up, down, or steady)
    """
    # If no components spcecify a non-default ramp_freq, then skip
    system = m.system
    comp = system.comp_map[cname]
    if not hasattr(comp, "ramp_freq") or comp.ramp_freq == 0:
        return pyo.Constraint.Skip

    return m.ramp_up_bin[cname, t] + m.ramp_down_bin[cname, t] + m.steady_bin[cname, t] == 1


# Resource Balance Constraints
def balance_rule(m: pyo.ConcreteModel, rname: str, t: int) -> pyo.Expression:
    """
    Calculate the balance rule for a specific resource at a given time step.

    This function creates a constraint ensuring the balance of the resource flow:
    production + storage discharge = consumption + storage charge.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The pyomo model containing the optimization variables and parameters.
    rname : str
        The name of the resource for which to calculate the balance.
    t : int
        The time step at which to calculate the balance.

    Returns
    -------
    pyo.Expression
        A Pyomo expression representing the balance constraint for the resource.
        The constraint ensures that production + storage discharge equals consumption + storage charge.
    """
    production = sum(
        m.flow[cname, rname, t]
        for cname in m.NON_STORAGE
        if rname in m.system.comp_map[cname].produces_by_name
    )

    consumption = sum(
        m.flow[cname, rname, t]
        for cname in m.NON_STORAGE
        if rname in m.system.comp_map[cname].consumes_by_name
    )

    storage_change = sum(
        m.discharge[s, t] - m.charge[s, t]
        for s in m.STORAGE
        if m.system.comp_map[s].resource.name == rname
    )
    return production - consumption + storage_change == 0


def storage_balance_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """
    Create an expression to ensure state of charge balance for a storage component at time t.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The Pyomo model instance containing system components and variables.
    sname : str
        The name of the storage component.
    t : int
        The time index at which to calculate the storage balance.

    Returns
    -------
    pyo.Expression
        A Pyomo expression representing the constraint that the state of charge at time t
        equals the previous state of charge plus charging (accounting for charging efficiency)
        minus discharging (accounting for discharging efficiency).

    Notes
    -----
    For the first time step, the previous state of charge is determined by the
    initial stored energy parameter of the storage component.
    The round-trip efficiency (rte) is applied as a square root to both charging and
    discharging, with charging multiplied by rte^0.5 and discharging divided by rte^0.5.
    """
    comp = m.system.comp_map[sname]
    if t == m.T.first():
        soc_prev = comp.initial_stored * np.max(comp.max_capacity_profile)
    else:
        soc_prev = m.soc[sname, m.T.prev(t)]
    return m.soc[sname, t] == soc_prev + (
        m.charge[sname, t] * comp.rte**0.5 - m.discharge[sname, t] / comp.rte**0.5
    )


def charge_limit_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """
    Create a rule for the maximum charging rate limit of a storage component.

    This function returns a pyomo expression that constrains the charging rate
    of a storage component to its maximum charging rate, which is defined as
    a fraction of its maximum capacity at the given timestep.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The Pyomo model being constructed
    sname : str
        The name of the storage component
    t : int
        The time step/period

    Returns
    -------
    pyo.Expression
        An expression stating that the charging rate at time t must be less than
        or equal to the maximum charging rate (as a proportion of maximum capacity)
    """
    comp: Storage = m.system.comp_map[sname]
    return m.charge[sname, t] <= comp.max_charge_rate * np.max(comp.max_capacity_profile)


def discharge_limit_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """
    Create an expression for the maximum discharge rate of a storage component.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The pyomo model containing the system and its components
    sname : str
        The name of the storage component
    t : int
        The time index for which to create the discharge limit constraint

    Returns
    -------
    pyo.Expression
        An expression representing the constraint that discharge at time t cannot exceed the maximum
        discharge rate times the maximum capacity of the storage component at the given timestep
    """
    comp: Storage = m.system.comp_map[sname]
    return m.discharge[sname, t] <= comp.max_discharge_rate * np.max(comp.max_capacity_profile)


def soc_limit_rule(m: pyo.ConcreteModel, sname: str, t: int) -> pyo.Expression:
    """
    Create an expression that constrains the state of charge (SOC) of a storage
    component to not exceed its maximum capacity at the given timestep.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The Pyomo model instance containing system components and variables
    sname : str
        The name of the storage component in the system
    t : int
        The time step index

    Returns
    -------
    pyo.Expression
        A Pyomo expression that limits SOC to the storage component's maximum capacity at the given timestep
    """
    comp: Storage = m.system.comp_map[sname]
    return m.soc[sname, t] <= comp.max_capacity_profile[t]


def periodic_storage_rule(m: pyo.ConcreteModel, sname: str) -> pyo.Constraint:
    """
    Enforce periodic storage level for a storage component.

    This constraint ensures that the state of charge (SOC) at the final time step
    equals the initial state of charge, respecting the `initial_stored` attribute.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The Pyomo model instance containing system components and variables.
    sname : str
        The name of the storage component.

    Returns
    -------
    pyo.Constraint
        A Pyomo constraint enforcing periodic storage level.
    """
    comp = m.system.comp_map[sname]
    if not comp.periodic_level:
        return pyo.Constraint.Skip

    # Enforce SOC at the final time step equals the initial SOC
    return m.soc[sname, m.T.last()] == comp.initial_stored * np.max(comp.max_capacity_profile)


def objective_rule(m: pyo.ConcreteModel) -> pyo.Expression:
    """
    Calculate the objective function expression for a price-taker optimization model.

    This function computes the total economic value from all system components by
    evaluating the cashflows associated with the dispatch decisions. Each cashflow
    is scaled according to its price profile and scaling parameters.

    Parameters
    ----------
    m : pyo.ConcreteModel
        The Pyomo model containing system components, dispatch variables, and time periods

    Returns
    -------
    pyo.Expression
        The objective function expression representing total economic value

    Notes
    -----
    The function iterates through all components in the system, accessing their
    cashflows and calculating the contribution to the objective based on:
    - The dispatch level of the component at each time period
    - The price profile associated with each cashflow
    - Scaling parameters (dprime and scalex) that allow for non-linear relationships
    """
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
