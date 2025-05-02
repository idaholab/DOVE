# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""

"""
from .interaction_spec import InteractionSpec
from .autospec import AutoSpec

class DemandSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("demands", baseNode=InteractionSpec.getInputSpecification())
    return cls

  def instantiate(self):
    """ """
    demand_args = {}
    demand_args["consumes"] = self.parameterValues.get("resource")
    return demand_args
