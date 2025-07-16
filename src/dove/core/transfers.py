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
- RatioTransfer: Simple linear relationship between input and output resources (e.g., efficiency)
- PolynomialTransfer: More complex non-linear relationship described by polynomial terms

These transfer functions can be used to model various energy conversion processes
including power plants, heat exchangers, fuel cells, and other technologies where
inputs are transformed into outputs with specific characteristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    import pyomo.environ as pyo

    from . import Resource

TransferFunc: TypeAlias = "RatioTransfer | PolynomialTransfer"


@dataclass()
class RatioTransfer:
    """
    A transfer class that enforces ratio relationships between multiple input and output resources.

    This class models the conversion of one or more resources to one or more other resources
    according to specified ratios between each. For example, it could represent energy conversion
    with less than 100% efficiency and multiple required inputs or material transformation that
    involves relevant waste products. This class is intended to be used to enforce relationships
    between input and output quantities as well as ratios between multiple different inputs and
    ratios between multiple different outputs. This is comparable to a chemical balance
    relationship, where A, B, C, and D are constant floats:
        A(input_resource_1) + B(input_resource_2) -> C(output_resource_1) + D(output_resource_2)

    Parameters
    ----------
    input_resources : dict[Resource, float]
        A dictionary keyed by the input resources to the component with values that are the
        relative amounts required of that resource to enable conversion to output resources.
    output_resources : Resource
        A dictionary keyed by the output resources to the component with values that are the
        relative amounts produced of that resource when the inputs are supplied.


    Examples
    --------
    Create a transfer that converts heat to electricity at 90% efficiency (assuming "heat" and
    "electricity" are both Resource instances and are both in MW):

    >>> transfer = RatioTransfer(
            input_resources={heat: 1.0},
            output_resources={electricity: 0.9},
        )

    Later, after component instantiation, the transfer can be used to evaluate a
    constraint with dispatch activity values:

    >>> transfer(inputs={"heat": 200}, outputs={"electricity": 180})
    [True]

    This means that the constraint for which this transfer can be used should be satisfied. This
    new transfer function can be added to a Component such as a Converter:

    >>> converter = Converter(
            name="converter",
            consumes=[heat],
            produces=[electricity],
            capacity_resource=electricity,
            max_capacity_profile=[100],
            transfer_fn=transfer,
        )

    Create a transfer that converts 1.8 units of heat and 1.0 units of electricity to 0.5 units of
    hydrogen. Note that these are fictional values. Assume "heat", "electricity", and "hydrogen"
    are all Resource instances:

    >>> transfer = RatioTransfer(
            input_resources={heat: 1.8, electricity: 1.0},
            output_resources={hydrogen: 0.5},
        )

    Later, after component instantiation, the transfer can be used to evaluate a
    constraint with dispatch activity values:

    >>> transfer(inputs={"heat": 180, "electricity": 100}, outputs={"hydrogen": 50})
    [True]
    """

    input_resources: dict[Resource, float]
    output_resources: dict[Resource, float]

    def __call__(
        self, inputs: dict[str, float], outputs: dict[str, float]
    ) -> list[bool] | list[pyo.Expression]:
        """
        Provide a list of whether various equality requirements between resources are met.

        This function returns a list of booleans (or a list of pyomo Expressions, if it is being
        used in a pyomo Constraint). These booleans refer to whether the ratio relationship
        specified at instantiation is being respected across the set of input and output resources.
        Effectively, if all the values in the list are True, then the ratios are being respected.
        The length of the list is:
            # of input resources + # of output resources - 1

        Parameters
        ----------
        inputs : dict[str, float]
            Dictionary mapping resource names to their input flow values.
        outputs : dict[str, float]
            Dictionary mapping resource names to their output flow values.

        Returns
        -------
        list[bool] | list[pyo.Expression]
            A list of booleans or equality espressions that must all be true if the transfer
            relationship is being respected by all the inputs and outputs.

        Raises
        ------
        ValueError
            If an input or output resource cannot be found in the dispatch variables
        """
        for input_res in self.input_resources:
            if input_res.name not in inputs:
                raise ValueError(
                    f"RatioTransfer: Input resource '{input_res.name}' "
                    "not found in the provided dispatch variable for inputs"
                )

        for output_res in self.output_resources:
            if output_res.name not in outputs:
                raise ValueError(
                    f"RatioTransfer: Output resource '{output_res.name}' "
                    "not found in the provided dispatch variable for outputs"
                )

        weighted_inputs = [inputs[res.name] / ratio for res, ratio in self.input_resources.items()]
        weighted_outputs = [
            outputs[res.name] / ratio for res, ratio in self.output_resources.items()
        ]
        weighted_values = weighted_inputs + weighted_outputs

        MIN_VALUES = 2
        if len(weighted_values) < MIN_VALUES:
            return []  # There are no requirements in order to satisfy this transfer function

        return [weighted_values[0] == val for val in weighted_values[1:]]


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

    def __call__(
        self, inputs: dict[str, float], outputs: dict[str, float]
    ) -> list[bool] | list[pyo.Expression]:
        """
        Calculate an expression that relates inputs to outputs for this transfer function.

        The function provides an equality expression such that the sum of all outputs equals the
        evaluated transfer function based on inputs. The transfer function is evaluated by
        computing each term (coefficient times product of input variables raised to their
        exponents) and summing them.

        Parameters
        ----------
        inputs : dict[str, float]
            Dictionary mapping resource names to their input values.
        outputs : dict[str, float]
            Dictionary mapping resource names to their output values.

        Returns
        -------
        list[bool] | list[pyo.Expression]
            A list containing a single boolean or expression that refers to whether the transfer
            relationship is being respected.
        """
        total_output = sum(outputs.values())
        expr = 0.0
        for coef, input_exponents in self.terms:
            term = coef
            for res, exp in input_exponents.items():
                term *= inputs[res.name] ** exp
            expr += term
        return [total_output == expr]
