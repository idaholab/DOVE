# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.models.price_taker.builder``
========================

Price Taker Builder Module

This module provides a builder class for creating price taker optimization models
within the DOVE framework. A price taker represents a market participant that
accepts energy market prices as given and optimizes operations accordingly.

The PriceTakerBuilder constructs a Pyomo optimization model with:
- Sets for components (storage and non-storage), resources, and time periods
- Variables for resource flows, state of charge, and charge/discharge rates
- Constraints for resource balances, capacity limits, and storage operations
- An economic objective function optimizing market participation

The model incorporates both standard generation/consumption components and
storage components with their associated charge/discharge dynamics and state
of charge tracking.

Notes
-----
The price taker model focuses on economic optimization of resource flows
without attempting to influence market prices.

See Also
dove.models.base.BaseModelBuilder : Parent class providing the base builder interface
"""

from typing import Any, Self

import pandas as pd
import pyomo.environ as pyo  # type: ignore[import-untyped]

from dove.models import register_builder
from dove.models.base import BaseModelBuilder

from . import rulelib as prl


@register_builder("price_taker")
class PriceTakerBuilder(BaseModelBuilder):
    """
    Builder class for creating price taker optimization models.

    This class implements the builder pattern to construct a price taker optimization
    model step by step. A price taker model represents a participant in an energy
    market that accepts prices as given and optimizes their operations accordingly.

    The builder adds sets, variables, constraints, and an objective function to
    the optimization model, and provides methods to solve it and extract results.

    Attributes
    ----------
    model : pyo.ConcreteModel
        The Pyomo concrete model being constructed.
    system : object
        The energy system being modeled, containing components, resources, and time indices.

    Examples
    --------
    >>> builder = PriceTakerBuilder(system)
    >>> model = builder.build().solve()
    >>> results = builder.extract_results()
    """

    def build(self) -> Self:
        """
        Build the price taker optimization model.

        Creates a Pyomo concrete model and adds the necessary sets, variables,
        constraints, and objective function to formulate the price taker
        optimization problem.

        Returns
        -------
        Self
            The builder instance, allowing for method chaining.
        """
        self.model = pyo.ConcreteModel()
        self.model.system = self.system

        self._add_sets()
        self._add_variables()
        self._add_constraints()
        self._add_objective()

        return self

    def solve(self, **kw: Any) -> pyo.ConcreteModel:
        """
        Solve the built optimization model.

        Parameters
        ----------
        **kw : Any
            Keyword arguments for the solver configuration.
            - solver : str, optional
                The solver to use for optimization, default is 'cbc'.

        Returns
        -------
        pyo.ConcreteModel
            The solved Pyomo model.
        """
        solver = pyo.SolverFactory(kw.get("solver", "cbc"))
        solver.solve(self.model)
        return self.model

    def extract_results(self) -> pd.DataFrame:
        """
        Extract results from the solved model into a DataFrame.

        Collects flow values for all resources produced or consumed by components,
        as well as state of charge and charge/discharge rates for storage components.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the optimization results with time index
            and columns for each component-resource flow and storage variables.
        """
        m = self.model
        data = {}
        T = self.system.time_index
        for comp in self.system.components:
            for res in comp.produces + comp.consumes:
                # Since everything is defined as positive flow, we need to flip the sign
                # to make it clear if the component is producing or consuming
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
        """
        Add sets to the optimization model.

        Creates sets for:
        - NON_STORAGE: Non-storage components
        - STORAGE: Storage components
        - R: Resources
        - T: Time periods (ordered)
        """
        non_storage_comp_names = self.model.system.non_storage_comp_names
        storage_comp_names = self.model.system.storage_comp_names

        self.model.NON_STORAGE = pyo.Set(initialize=non_storage_comp_names)
        self.model.STORAGE = pyo.Set(initialize=storage_comp_names)
        self.model.R = pyo.Set(initialize=[r.name for r in self.system.resources])
        self.model.T = pyo.Set(initialize=self.system.time_index, ordered=True)

    def _add_variables(self) -> None:
        """
        Add decision variables to the optimization model.

        Creates variables for:
        - flow: Resource flow for non-storage components
        - SOC: State of charge for storage components
        - charge: Charging activity for storage components
        - discharge: Discharging activity for storage components
        """
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
        """
        Add constraints to the optimization model.

        Adds various constraints including:
        - Resource transfer constraints
        - Capacity constraints
        - Minimum capacity constraints
        - Fixed profile constraints
        - Resource balance constraints
        - Storage balance constraints
        - Charging/discharging limits
        - State of charge limits
        """
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
        """
        Add the objective function to the optimization model.

        Sets a maximization objective based on the price taker objective rule
        defined in the rulelib module.
        """
        self.model.objective = pyo.Objective(rule=prl.objective_rule, sense=pyo.maximize)
