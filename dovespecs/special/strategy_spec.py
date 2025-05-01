# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class StrategySpec(SimpleNodeSpec):
  """ """

  node_name = "strategy"
  content_type = InputTypes.StringType
  description = r"""
  control strategy for operating the storage. If not specified,
  uses a perfect foresight strategy.
  """
