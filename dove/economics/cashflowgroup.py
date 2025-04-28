# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Defines the Economics entity.
Each component (or source?) can have one of these to describe its economics.
"""
from . import CashFlow

from ravenframework.utils import InputData, InputTypes

class CashFlowGroup:
  """
  Container for multiple CashFlows with utility methods.
  """
  tag = "economics"

  @classmethod
  def get_input_specs(cls) -> type[InputData.ParameterInput]:
    """
    Collects input specifications for this class.
    @In, None
    @Out, input_specs, ParameterInput, specs
    """
    specs = InputData.parameterInputFactory(
      "economics",
      ordered=False,
      baseNode=None,
      descr=r"""this node is where all the economic information about this
                component is placed.""",
    )

    specs.addParam(
      "lifetime",
      param_type=InputTypes.IntegerType, # type: ignore
      required=False,
      default="100",
      descr=r"""indicates the number of \emph{cycles} (often \emph{years}) this
                unit is expected to operate before replacement. Replacement is
                represented as overnight capital cost in the year the component
                is replaced.""",
    )

    specs.addSub(CashFlow.get_input_specs())
    return specs

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

  def read_input(self, specs: InputData.ParameterInput) -> None:
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

