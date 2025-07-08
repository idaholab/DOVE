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
- RatioTransfer: Simple linear relationship between one input and one output (e.g., efficiency)
- MultiRatioTransfer: Linear relationship between multiple inputs and outputs
- PolynomialTransfer: More complex non-linear relationship described by polynomial terms

These transfer functions can be used to model various energy conversion processes
including power plants, heat exchangers, fuel cells, and other technologies where
inputs are transformed into outputs with specific characteristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from . import Resource

TransferFunc: TypeAlias = "RatioTransfer | MultiRatioTransfer | PolynomialTransfer"


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

    Later, after component instantiation, the transfer can be used to evaluate a
    constraint with dispatch activity values:

    >>> transfer(inputs={"electricity": 100}, outputs={"heat": 95})
    [95, 95]

    Since these values are equal, the constraint should be satisfied.
    """

    input_res: Resource
    output_res: Resource
    ratio: float = 1.0

    def __call__(self, inputs: dict[str, float], outputs: dict[str, float]) -> list[float]:
        """
        Provide values for a constraint that enforces the output to be a fixed ratio of the input.

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
        list[float]
            A list of values that must be equal for the transfer constraint to be satisfied.

        Raises
        ------
        ValueError
            If neither input nor output resource is found in the provided dictionaries.
        """
        has_input = self.input_res.name in inputs
        has_output = self.output_res.name in outputs

        if has_input and has_output:
            return [outputs[self.output_res.name], self.ratio * inputs[self.input_res.name]]

        elif has_output and not has_input:
            # Source: output = output (tautology)
            return []

        elif has_input and not has_output:
            # Sink: input = input (tautology)
            return []

        else:
            raise ValueError(
                f"RatioTransfer could not find either input '{self.input_res}' "
                f"or output '{self.output_res}' in the provided dispatch variables."
            )


@dataclass()
class MultiRatioTransfer:
    """
    A transfer class that enforces ratio relationships between multiple input and output resources.

    This class models the conversion of one or more resources to one or more other resources with
    specified ratios. For example, it could represent energy conversion with multiple required
    inputs or material transformation that involves relevant waste products. This class is intended
    to be used to enforce relationships between input and output quantities as well as ratios between
    multiple different inputs and ratios between multiple different outputs.

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
    Create a transfer that converts 1.8 units of heat and 1.0 units of electricity to 0.5 units of
    hydrogen (assuming "heat", "electricity", and "hydrogen" are all Resource instances):

    >>> transfer = MultiRatioTransfer(
            input_resources={heat: 1.8, electricity: 1.0},
            output_resources={hydrogen: 0.5},
        )

    Later, after component instantiation, the transfer can be used to evaluate a
    constraint with dispatch activity values:

    >>> transfer(inputs={"heat": 180, "electricity": 100}, outputs={"hydrogen": 50})
    [100, 100, 100]

    Since these values are all equal, the constraint should be satisfied.
    """

    input_resources: dict[Resource, float]
    output_resources: dict[Resource, float]

    def __call__(self, inputs: dict[str, float], outputs: dict[str, float]) -> list[float]:
        """
        Provide values for inputs and outputs adjusted by the respective required ratios for each.

        This function returns a list of input and output quantities, adjusted by (divided by) the
        ratios provided.

        Parameters
        ----------
        inputs : dict[str, float]
            Dictionary mapping resource names to their input flow values.
        outputs : dict[str, float]
            Dictionary mapping resource names to their output flow values.

        Returns
        -------
        list[float]
            A list of values that must be equal for the transfer constraint to be satisfied.

        Raises
        ------
        ValueError
            If an input or output resource cannot be found in the dispatch variables
        """
        for input_res in self.input_resources:
            if input_res.name not in inputs:
                raise ValueError(
                    f"MultiRatioTransfer: Input resource '{input_res.name}' "
                    "not found in the provided dispatch variable for inputs"
                )

        for output_res in self.output_resources:
            if output_res.name not in outputs:
                raise ValueError(
                    f"MultiRatioTransfer: Output resource '{output_res.name}' "
                    "not found in the provided dispatch variable for outputs"
                )

        weighted_inputs = [inputs[res.name] / ratio for res, ratio in self.input_resources.items()]
        weighted_outputs = [
            outputs[res.name] / ratio for res, ratio in self.output_resources.items()
        ]
        return weighted_inputs + weighted_outputs


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

    def __call__(self, inputs: dict[str, float], outputs: dict[str, float]) -> list[float]:
        """
        Provide values for a constraint that relates inputs to outputs for this transfer function.

        The function provides values for an equality constraint such that the sum of all outputs
        equals the evaluated transfer function based on inputs. The transfer function is evaluated
        by computing each term (coefficient times product of input variables raised to their
        exponents) and summing them.

        Parameters
        ----------
        inputs : dict[str, float]
            Dictionary mapping resource names to their input values.
        outputs : dict[str, float]
            Dictionary mapping resource names to their output values.

        Returns
        -------
        list(float)
            A list of values that must be equal for the transfer constraint to be satisfied.
        """
        total_output = sum(outputs.values())
        expr = 0.0
        for coef, input_exponents in self.terms:
            term = coef
            for res, exp in input_exponents.items():
                term *= inputs[res.name] ** exp
            expr += term
        return [total_output, expr]
