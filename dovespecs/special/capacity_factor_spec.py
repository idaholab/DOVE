# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Capacity Factor Input Specification
"""

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class CapacityFactorSpec(SimpleNodeSpec):
  """ """

  node_name = "capacity_factor"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  the actual value at which this component can act, as a unitless
  fraction of total rated capacity. Note that these factors are applied
  within the dispatch optimization; we assume that the capacity factor
  is not a variable in the outer optimization.
  """
