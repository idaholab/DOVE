# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.transfers``
========================

Core transfer functions for resource conversion in the DOVE optimization framework.

This module provides classes that model mathematical relationships between input
and output resources in energy systems. These transfer functions represent physical
or economic transformations such as energy conversion, efficiency losses, or
material transformations.

The module defines two main transfer function types:
- RatioTransfer: Simple linear relationship between inputs and outputs (e.g., efficiency)
- PolynomialTransfer: More complex non-linear relationship described by polynomial terms

These transfer functions can be used to model various energy conversion processes
including power plants, heat exchangers, fuel cells, and other technologies where
inputs are transformed into outputs with specific characteristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

import pyomo.environ as pyo  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from . import Resource

TransferFunc: TypeAlias = "RatioTransfer | PolynomialTransfer"


@dataclass
class RatioTransfer:
    """
    A transfer class that enforces a ratio relationship between input and output resources.

    This class models the conversion of one resource to another with a specified ratio.
    For example, it could represent energy conversion efficiency or material transformation.

    Parameters
    ----------
    input_res : Resource
        The input resource object.
    output_res : Resource
        The output resource object.
    ratio : float, default=1.0
        The conversion ratio from input to output.
        A ratio of 1.0 means the output equals the input.
        A ratio of 0.9 means 90% of input becomes output (10% loss).
        A ratio > 1.0 means the output is amplified relative to input.

    Examples
    --------
    Create a transfer that converts electricity to heat with 95% efficiency:

    >>> transfer = RatioTransfer(
            input_res=Resource("electricity"),
            output_res=Resource("heat"),
            ratio=0.95
        )

    Later, after component instantiation, the transfer can be used evaluate a
    constraint with dispatch activity values:

    >>> transfer(inputs={"electricity": 100}, outputs={"heat": 95})
    True
    """

    input_res: Resource
    output_res: Resource
    ratio: float = 1.0

    def __call__(self, inputs: dict[str, float], outputs: dict[str, float]) -> pyo.Expression:
        """
        Create a constraint that enforces the output value to be a fixed ratio of the input value.

        This method handles three cases:
        1. Both input and output resources exist: enforce output == ratio * input
        2. Only output resource exists (Source case): skip constraint as it's dispatched 1:1
        3. Only input resource exists (Sink case): skip constraint as it's dispatched 1:1

        Parameters
        ----------
        inputs : dict[str, float]
            Dictionary mapping resource names to their input flow values.
        outputs : dict[str, float]
            Dictionary mapping resource names to their output flow values.

        Returns
        -------
        pyo.Expression
            A constraint enforcing the ratio relation, or Constraint.Skip for Source/Sink cases.

        Raises
        ------
        ValueError
            If neither input nor output resource is found in the provided dictionaries.
        """
        has_input = self.input_res.name in inputs
        has_output = self.output_res.name in outputs

        if has_input and has_output:
            return outputs[self.output_res.name] == self.ratio * inputs[self.input_res.name]

        elif has_output and not has_input:
            # Source: output = output (tautology)
            return pyo.Constraint.Skip

        elif has_input and not has_output:
            # Sink: input = input (tautology)
            return pyo.Constraint.Skip

        else:
            raise ValueError(
                f"RatioTransfer could not find either input '{self.input_res}' "
                f"or output '{self.output_res}' in the provided dispatch variables."
            )


@dataclass
class PolynomialTransfer:
    """
    Represents a polynomial transfer function that maps input resources to output resources.

    This class models a polynomial relationship between inputs and outputs, where the output
    is a sum of terms, each term being a coefficient multiplied by input resources raised to
    specified powers.

    Parameters
    ----------
    terms : list[tuple[float, dict[Resource, int]]]
        A list of terms in the polynomial.
        Each term is represented as a tuple containing:
        - A coefficient (float)
        - A dictionary (dict[Resource, int]) mapping Resource objects to their exponents in the term.

    Attributes
    ----------
    terms : list[tuple[float, dict[Resource, int]]]
        A list of terms in the polynomial.

    Examples
    --------
    A combined cycle power plant model with efficiency curve:
    output = 0.35 * natural_gas^1 + 0.05 * natural_gas^0.5
    would be represented as:

    >>> PolynomialTransfer([
            (0.35, {natural_gas: 1}),
            (0.05, {natural_gas: 0.5})
        ])
    """

    terms: list[tuple[float, dict[Resource, int]]]

    def __call__(self, inputs: dict[str, float], outputs: dict[str, float]) -> pyo.Expression:
        """
        Create a constraint expression that relates inputs to outputs for this transfer function.

        The function constructs a constraint where the sum of all outputs equals the evaluated
        transfer function based on inputs. The transfer function is evaluated by computing
        each term (coefficient times product of input variables raised to their exponents)
        and summing them.

        Parameters
        ----------
        inputs : dict[str, float]
            Dictionary mapping resource names to their input values.
        outputs : dict[str, float]
            Dictionary mapping resource names to their output values.

        Returns
        -------
        pyo.Expression
            A Pyomo expression representing the constraint: total_output == f(inputs)
            where f is the transfer function defined by the terms.
        """
        total_output = sum(outputs.values())
        expr = 0.0
        for coef, input_exponents in self.terms:
            term = coef
            for res, exp in input_exponents.items():
                term *= inputs[res.name] ** exp
            expr += term
        return total_output == expr
