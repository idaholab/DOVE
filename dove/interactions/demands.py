# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Demands interaction module
"""
from ravenframework.utils.InputData import ParameterInput
from . import Interaction

class Demand(Interaction):
  """
  Explains a particular interaction, where a resource is demanded
  """
  tag = "demands"  # node name in input file
  @classmethod
  def get_input_specs(cls) -> type[ParameterInput]:
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    specs = super().get_input_specs()
    return specs

  def __init__(self, **kwargs) -> None:
    """
    Constructor
    @ In, kwargs, dict, arguments
    @ Out, None
    """
    Interaction.__init__(self, **kwargs)
    self.tracking_vars = ["production"]

  def read_input(self, specs: ParameterInput, comp_name: str) -> None:
    """
    Sets settings from input file
    @ In, specs, InputData, specs
    @ In, comp_name, string, name of component this Interaction belongs to
    @ Out, None
    """
    Interaction.read_input(self, specs, comp_name)
    self.inputs = set(specs.parameterValues["resource"])

  def print_me(self, tabs: int = 0, tab: str = "  ") -> None:
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    print(pre + "Demand/Load:")
    print(pre + "  demands:", self.inputs)
    print(pre + "  capacity:", self._capacity)
