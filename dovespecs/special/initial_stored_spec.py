# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class InitialStoredSpec(SimpleNodeSpec):
  """ """

  node_name = "initial_stored"
  content_type = InputTypes.FloatOrIntType
  description = r"""
        indicates what percent of the storage unit is full at the start
        of each optimization sequence, from 0 to 1. \default{0.0}.
        """
