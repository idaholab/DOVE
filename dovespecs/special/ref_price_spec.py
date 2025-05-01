# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec
from ravenframework.utils.InputData import InputTypes


@register_spec
class ReferencePriceSpec(SimpleNodeSpec):
  """ """

  node_name = "reference_price"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  indicates the cash value of the reference number of units sold.
  corresponds to $\alpha$ in the CashFlow equation. If \xmlNode{reference_driver}
  is 1, then this is the price-per-unit for the CashFlow.
  """
  params = {
    "levelized": (
      InputTypes.BoolType,
      False,
      "False",
      r"""
      indicates whether HERON and TEAL are meant to solve for the levelized
      price related to this cashflow.
      """,
    )
  }
