# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class DriverSpec(SimpleNodeSpec):
  """ """

  node_name = "driver"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  indicates the main driver for this CashFlow, such as the number of
  units sold or the size of the constructed unit. Corresponds to $D$
  in the CashFlow equation.
  """
