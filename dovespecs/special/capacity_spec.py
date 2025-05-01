# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from ..simple_spec import SimpleNodeSpec
from .registry import register_spec


@register_spec
class CapacitySpec(SimpleNodeSpec):
  """"""

  node_name = "capacity"
  content_type = InputTypes.FloatOrIntType
  description = r"""
  the maximum value at which this component can act, in units corresponding
  to the indicated resource.
  """
  params = {
    "resource": (
      InputTypes.StringType,
      False,
      None,
      r"""
      indicates the resource that defines the capacity of this component's
      operation. For example, if a component consumes steam and electricity
      to produce hydrogen, the capacity of the component can be defined by
      the maximum steam consumable, maximum electricity consumable, or maximum
      hydrogen producable. Any choice should be nominally equivalent, but
      determines the units of the value of this node.
      """,
    )
  }
