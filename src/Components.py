# Copyright 2020, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Module
"""
from DOVE.src import Base
from DOVE.src.Economics import CashFlowGroup, CashFlow
from DOVE.src.Interactions import Demand, Producer, Storage

from ravenframework.utils import InputData, InputTypes

class Component(Base):
  """
  Represents a system component in the grid analysis. Each component has a
  single "interaction" that describes what it can do (produce, store, demand)
  and a single CashFlowGroup which is a container for component associated cashflows.
  """
  @classmethod
  def get_input_specs(cls) -> type[InputData.ParameterInput]:
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    input_specs = InputData.parameterInputFactory(
      "Component",
      ordered=False,
      baseNode=None,
      descr="""defines a component as an element of the grid system.
               Components are defined by the action they perform such as
              \\xmlNode{produces} or \\xmlNode{consumes}; see details below.""",
    )

    input_specs.addParam(
      "name",
      param_type=InputTypes.StringType,
      required=True,
      descr=r"""identifier for the component. This identifier will be used to
                generate variables and relate signals to this component throughout
                the DOVE analysis.""",
    )

    input_specs.addSub(Producer.get_input_specs())
    input_specs.addSub(Storage.get_input_specs())
    input_specs.addSub(Demand.get_input_specs())
    input_specs.addSub(CashFlowGroup.get_input_specs())
    return input_specs

  def __init__(self, **kwargs) -> None:
    """
    Constructor
    @ In, kwargs, dict, optional, arguments to pass to other constructors
    @ Out, None
    """
    Base.__init__(self, **kwargs)
    self.name = "placeholder" # Name is required, so just initialize with a temp name.
    self._interaction = None
    self._economics = None
    self.levelized_meta = {}

  def __repr__(self) -> str:
    """
    String representation.
    @ In, None
    @ Out, __repr__, string representation
    """
    return f'<DOVE Component "{self.name}">'

  def read_input(self, xml) -> None:
    """
    Sets settings from input file
    @In, xml, xml.etree.ElementTree.Element, component information from xml input file.
    @Out, None
    """
    # get specs for allowable inputs
    specs = self.get_input_specs()()
    specs.parseNode(xml)
    self.name = specs.parameterValues["name"]
    interaction_map = {
      "produces": Producer,
      "stores": Storage,
      "demands": Demand
    }

    found_interactions: dict
    not_found_in_spec: list
    found_interactions, not_found_in_spec = specs.findNodesAndExtractValues(interaction_map.keys())
    if all((interaction == 'no-default' for interaction in found_interactions.values())):
      self.raiseAnError(IOError, f"No interaction found for Component '{self.name}'")
    elif len(not_found_in_spec) < 2:
      self.raiseAnError(IOError, f"A Component can only have one interaction! Check Component '{self.name}'")

    for item in specs.subparts:
      item_name = item.getName()
      if item_name in interaction_map:
        interaction_instance = interaction_map[item_name](messageHandler=self.messageHandler)
        interaction_instance.read_input(item, self.name)
        self._interaction = interaction_instance
      elif item_name == 'economics':
        cashflows = CashFlowGroup(self, messageHander=self.messageHandler)
        cashflows.read_input(item)
        self._economics = cashflows

  @property
  def interaction(self) -> Demand | Producer | Storage:
    if self._interaction is None:
      raise AttributeError(f"component '{self.name}' has no attribute 'interaction'!")
    return self._interaction

  @property
  def economics(self) -> CashFlowGroup:
    if self._economics is None:
      raise AttributeError(f"component '{self.name}' has no attribute 'economics'!")
    return self._economics

  def print_me(self, tabs=0, tab="  ") -> None:
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    self.raiseADebug(pre + "Component:")
    self.raiseADebug(pre + "  name:", self.name)
    self.interaction.print_me(tabs=tabs + 1, tab=tab)

  def set_levelized_cost_meta(self, cashflows) -> None:
    """
    Create a dictionary for determining the correct resource to use per cashflow
    when using a levelized inner objective.

    NOTE: This is only an option when selecting levelized cost as an econ metric.

    :param cashflows: List of Interaction instances.
    :type cashflows: list
    :return: None
    """
    for cf in cashflows:
      tracker = cf.get_driver()._vp.get_tracking_var()
      resource = cf.get_driver()._vp.get_resource()
      self.levelized_meta[cf.name] = {tracker: resource}
