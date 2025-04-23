import numpy as np

from DOVE.src.Interactions.Interaction import Interaction
from ravenframework.utils.InputData import ParameterInput


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
    self._tracking_vars: list[str] = ["production"]
    self._demands: list[str] = []

  def read_input(self, specs, comp_name):
    """
    Sets settings from input file
    @ In, specs, InputData, specs
    @ In, comp_name, string, name of component this Interaction belongs to
    @ Out, None
    """
    # specs were already checked in Component
    # must set demands first, so that "capacity" can access it
    Interaction.read_input(self, specs, comp_name)
    self._demands = specs.parameterValues["resource"]

  def get_inputs(self) -> set[str]:
    """
    Returns the set of resources that are inputs to this interaction.
    @ In, None
    @ Out, inputs, set, set of inputs
    """
    inputs = Interaction.get_inputs(self)
    inputs.update(np.atleast_1d(self._demands))
    return inputs

  def print_me(self, tabs: int = 0, tab: str = "  ") -> None:
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    self.raiseADebug(pre + "Demand/Load:")
    self.raiseADebug(pre + "  demands:", self._demands)
    self.raiseADebug(pre + "  capacity:", self._capacity)
