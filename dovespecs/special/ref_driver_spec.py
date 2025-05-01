# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class ReferenceDriverSpec(SimpleNodeSpec):
  """ """

  node_name = "reference_driver"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  determines the number of units sold to which the \xmlNode{reference_price}
  refers. Corresponds to $\prime D$ in the CashFlow equation.
  """
