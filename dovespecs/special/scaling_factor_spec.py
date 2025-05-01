# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class ScalingFactorSpec(SimpleNodeSpec):
  """ """

  node_name = "scaling_factor_x"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  determines the scaling factor for this CashFlow. Corresponds to
  $x$ in the CashFlow equation. If $x$ is less than one, the per-unit
  price decreases as the units sold increases above the \xmlNode{reference_driver},
  and vice versa.
  """
