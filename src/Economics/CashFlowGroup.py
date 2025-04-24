"""
Defines the Economics entity.
Each component (or source?) can have one of these to describe its economics.
"""
from DOVE.src import Base
from DOVE.src.Economics.CashFlow import CashFlow

from ravenframework.utils import InputData, InputTypes

class CashFlowGroup(Base):
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

    lifetime_spec = InputData.parameterInputFactory(
      "lifetime",
      contentType=InputTypes.IntegerType,
      descr=r"""indicates the number of \emph{cycles} (often \emph{years}) this
                unit is expected to operate before replacement. Replacement is
                represented as overnight capital cost in the year the component
                is replaced.""",
    )

    specs.addSub(lifetime_spec)
    specs.addSub(CashFlow.get_input_specs())
    return specs

  def __init__(self, component, **kwargs):
    """
    Constructor.
    @ In, component, Component, object to which this group belongs
    @ Out, None
    """
    Base.__init__(self, **kwargs)
    self.name = component.name
    self._component = component  # component this one
    self._lifetime: int | None = None  # lifetime of the component
    self._cash_flows: list[CashFlow] = []

  def read_input(self, specs: InputData.ParameterInput) -> None:
    """
    Sets settings from input file
    @ In, source, InputData.ParameterInput, input from user
    @ Out, None
    """
    for item in specs.subparts:
      match item.getName():
        case "lifetime":
          self._lifetime = item.value
        case "CashFlow":
          new = CashFlow(self._component)
          new.read_input(item)
          self._cash_flows.append(new)

    if self._lifetime is None:
      self.raiseAnError(IOError, f'Component "{self.name}" is missing its <lifetime> node!')

  @property
  def component(self):
    return self._component

  @property
  def lifetime(self) -> int:
    if self._lifetime is None:
      raise AttributeError(f"component '{self._component.name}' economics object has no attribute 'lifetime'!")
    return self._lifetime

  @property
  def cashflows(self) -> list[CashFlow]:
    return self._cash_flows

  def evaluate_cfs(self, activity, meta, marginal=False):
    pass

