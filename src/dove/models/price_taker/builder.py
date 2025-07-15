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
        T = self.system.dispatch_window
        for comp in self.system.components:
            for res in comp.produces + comp.consumes:
                # Since everything is defined as positive flow, we need to flip the sign
                # to make it clear if the component is producing or consuming
                sign = -1 if res in comp.consumes else 1
                direction = "consumes" if sign == -1 else "produces"
                vals = [pyo.value(m.flow[comp.name, res.name, t]) * sign for t in T]
                data[f"{comp.name}_{res.name}_{direction}"] = vals

            if comp.name in m.STORAGE:
                data[f"{comp.name}_SOC"] = [pyo.value(m.soc[comp.name, t]) for t in T]
                data[f"{comp.name}_charge"] = [pyo.value(m.charge[comp.name, t]) for t in T]
                data[f"{comp.name}_discharge"] = [pyo.value(m.discharge[comp.name, t]) for t in T]
        data["objective"] = [pyo.value(m.objective)]
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
        self.model.T = pyo.Set(initialize=self.system.dispatch_window, ordered=True)

    def _add_variables(self) -> None:
        """
        Add decision variables to the optimization model.

        Creates variables for:
        - flow: Resource flow for non-storage components
        - SOC: State of charge for storage components
        - charge: Charging activity for storage components
        - discharge: Discharging activity for storage components
        - ramp_up/ramp_down: Track ramping between time periods
        - ramp_up_bin/ramp_down_bin: Binary indicators for ramping events
        - steady_bin: Binary indicator for steady state operation
        """
        m = self.model
        m.flow = pyo.Var(m.NON_STORAGE, m.R, m.T, within=pyo.NonNegativeReals)

        # Storage Variables
        m.soc = pyo.Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)
        m.charge = pyo.Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)
        m.discharge = pyo.Var(m.STORAGE, m.T, within=pyo.NonNegativeReals)

        # Don't add ramping variables if no component has ramp frequency
        # This is to avoid unnecessary complexity in the model
        has_ramp_freq = any(
            hasattr(comp, "ramp_freq") and comp.ramp_freq > 0 for comp in self.system.components
        )
        if has_ramp_freq:
            # `ramp_up` and `ramp_down` vars are made for the sole purpose of tracking ramp events when
            # `ramp_freq` > 0. They are not meant to be thought of as representing physical flows within
            # the model, but only as a way of managing `flow` for binary events. The real use for
            # `ramp_up` and `ramp_down` is when the binary vars set them to 0 which forces `flow` to 0.
            # These variables are not meant to be thought of as flow differential, so don't try to use
            # them in any objective functions.
            m.ramp_up = pyo.Var(m.NON_STORAGE, m.T, within=pyo.NonNegativeReals)
            m.ramp_down = pyo.Var(m.NON_STORAGE, m.T, within=pyo.NonNegativeReals)
            m.ramp_up_bin = pyo.Var(m.NON_STORAGE, m.T, within=pyo.Binary)
            m.ramp_down_bin = pyo.Var(m.NON_STORAGE, m.T, within=pyo.Binary)
            m.steady_bin = pyo.Var(m.NON_STORAGE, m.T, within=pyo.Binary)

    def _add_constraints(self) -> None:
        """
        Add constraints to the optimization model.

        Adds various constraints including:
        - Resource transfer constraints
        - Capacity constraints
        - Minimum constraints
        - Resource balance constraints
        - Storage balance constraints
        - Charging/discharging limits
        - State of charge limits
        - Ramping constraints (rate limits and frequency limits)
        - Steady state definition and state selection
        """
        m = self.model

        m.transfer = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.transfer_rule)
        m.capacity = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.capacity_rule)
        m.minimum = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.minimum_rule)

        m.resource_balance = pyo.Constraint(m.R, m.T, rule=prl.balance_rule)

        # Storage Constraints
        m.storage_balance = pyo.Constraint(m.STORAGE, m.T, rule=prl.storage_balance_rule)
        m.charge_limit = pyo.Constraint(m.STORAGE, m.T, rule=prl.charge_limit_rule)
        m.discharge_limit = pyo.Constraint(m.STORAGE, m.T, rule=prl.discharge_limit_rule)
        m.soc_limit = pyo.Constraint(m.STORAGE, m.T, rule=prl.soc_limit_rule)
        m.periodic_storage = pyo.Constraint(m.STORAGE, rule=prl.periodic_storage_rule)

        # Ramp Constraints
        m.ramp_up_limit = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_up_rule)
        m.ramp_down_limit = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_down_rule)

        # Ramp Frequency Constraints
        m.ramp_track_up = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_track_up_rule)
        m.ramp_track_down = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_track_down_rule)
        m.ramp_bin_up = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_bin_up_rule)
        m.ramp_bin_down = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_bin_down_rule)
        m.state_selection = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.state_selection_rule)
        m.steady_state_upper = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.steady_state_upper_rule)
        m.steady_state_lower = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.steady_state_lower_rule)
        m.ramp_freq_window = pyo.Constraint(m.NON_STORAGE, m.T, rule=prl.ramp_freq_window_rule)

    def _add_objective(self) -> None:
        """
        Add the objective function to the optimization model.

        Sets a maximization objective based on the price taker objective rule
        defined in the rulelib module.
        """
        self.model.objective = pyo.Objective(rule=prl.objective_rule, sense=pyo.maximize)
