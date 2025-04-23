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
    @ In, component, CashFlowUser instance, object to which this group belongs
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
    @ In, xml, bool, if True then XML is passed in, not input data
    @ Out, None
    """
    for item in specs.subparts:
      item_name = item.getName()
      if item_name == "lifetime":
        self._lifetime = item.value
      elif item_name == "CashFlow":
        new = CashFlow(self._component)
        new.read_input(item)
        self._cash_flows.append(new)

    if self._lifetime is None:
      self.raiseAnError(IOError, f'Component "{self.name}" is missing its <lifetime> node!')

  def get_crossrefs(self):
    """
    Provides a dictionary of the entities needed by this cashflow group to be evaluated
    @ In, None
    @ Out, crossrefs, dict, dictionary of crossreferences needed (see ValuedParams)
    """
    crossrefs = dict((cf, cf.get_crossrefs()) for cf in self._cash_flows)
    return crossrefs

  def set_crossrefs(self, refs):
    """
    Provides links to entities needed to evaluate this cash flow group.
    @ In, refs, dict, reference entities
    @ Out, None
    """
    # set up pointers
    for cf in list(refs.keys()):
      for try_match in self._cash_flows:
        if try_match == cf:
          try_match.set_crossrefs(refs.pop(try_match))
          break
      else:
        cf.set_crossrefs({})

  def evaluate_cfs(self, activity, meta, marginal=False):
    """
    Calculates the incremental cost of a particular system configuration.
    @ In, activity, XArray.DataArray, array of driver-centric variable values
    @ In, meta, dict, additional user-defined meta
    @ In, marginal, bool, optional, if True then only get marginal cashflows (e.g. recurring hourly)
    @ Out, cost, dict, cash flow evaluations
    """
    # combine all cash flows into single cash flow evaluation
    if marginal:
      # FIXME assuming 'year' is the only non-marginal value
      # FIXME why is it "repeating" and not "Recurring"?
      cost = dict(
        (cf.name, cf.evaluate_cost(activity, meta))
        for cf in self.get_cashflows()
        if (cf.get_type() == "repeating" and cf.get_period() != "year")
      )
    else:
      cost = dict(
        (cf.name, cf.evaluate_cost(activity, meta)) for cf in self.get_cashflows()
      )
    return cost

  def get_cashflows(self) -> list[CashFlow]:
    """
    Getter.
    @ In, None
    @ Out, cashflow, list, cash flows for this cashflow group (ordered)
    """
    return self._cash_flows

  def get_component(self):
    """
    Return the cash flow user that owns this group
    @ In, None
    @ Out, component, CashFlowUser instance, owner
    """
    return self._component

  def get_lifetime(self):
    """
    Provides the lifetime of this cash flow user.
    @ In, None
    @ Out, lifetime, int, lifetime
    """
    return self._lifetime

