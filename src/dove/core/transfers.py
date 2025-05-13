# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""

"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence, TypeAlias, TYPE_CHECKING

from pyomo.environ import Constraint

if TYPE_CHECKING:
  from . import Resource

TransferFunc : TypeAlias = "Monomial | Polynomial | Ratio"


@dataclass
class RatioTransfer:
    input_res: str
    output_res: str
    ratio: float = 1.0

    def __call__(self, inputs: dict[str, float], outputs: dict[str, float]):
        """
        Enforce output = ratio * input.
        If both input and output are present, enforce: output == ratio * input.
        If only one is present, assume the dispatch is done externally (Source/Sink case).
        """
        has_input = self.input_res in inputs
        has_output = self.output_res in outputs

        if has_input and has_output:
            return outputs[self.output_res] == self.ratio * inputs[self.input_res]

        elif has_output and not has_input:
            # Source: output = output (tautology)
            return Constraint.Skip

        elif has_input and not has_output:
            # Sink: input = input (tautology)
            return Constraint.Skip

        else:
            raise ValueError(
                f"RatioTransfer could not find either input '{self.input_res}' "
                f"or output '{self.output_res}' in the provided dispatch variables."
            )

@dataclass
class PolynomialTransfer:
    terms: list[tuple[float, dict[str, int]]]  # [(coefficient, {resource: exponent, ...}), ...]

    def __call__(self, inputs, outputs):
        total_output = sum(outputs.values())
        expr = 0
        for coef, input_exponents in self.terms:
            term = coef
            for res, exp in input_exponents.items():
                term *= inputs[res] ** exp
            expr += term
        return total_output == expr
