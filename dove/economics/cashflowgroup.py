# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Defines the Economics entity.
Each component (or source?) can have one of these to describe its economics.
"""
from . import CashFlow

class CashFlowGroup:
  """
  Container for multiple CashFlows with utility methods.
  """
  tag = "economics"


  def __init__(self, component, **kwargs):
    """
    Constructor.
    @ In, component, Component, object to which this group belongs
    @ Out, None
    """
    self.name = component.name
    self._component = component  # component this one
    self.lifetime: int | None = None  # lifetime of the component
    self.cashflows: list[CashFlow] = []

  def read_input(self, specs) -> None:
    """
    Sets settings from input file
    @ In, source, InputData.ParameterInput, input from user
    @ Out, None
    """
    self.lifetime = specs.parameterValues.get("lifetime", 100)
    for item in specs.subparts:
      match item.getName():
        case "CashFlow":
          new = CashFlow(self._component)
          new.read_input(item)
          self.cashflows.append(new)

    if self.lifetime is None:
      raise IOError(f'Component "{self.name}" is missing its <lifetime> node!')


  def evaluate_cfs(self, activity, meta, marginal=False):
    pass

