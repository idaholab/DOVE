# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class MinimumSpec(SimpleNodeSpec):
  """"""

  node_name = "minimum"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  provides the minimum value at which this component can act, in units of 
  the indicated resource.
  """
  params = {
    "resource": (
      InputTypes.StringType,
      False,
      None,
      r"""
      indicates the resource that defines the minimum activity level for this
      component, as with the component's capacity.
      """,
    )
  }
