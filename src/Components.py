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
      self.raiseAnError(NotImplementedError, f"No interaction found for Component '{self.name}'")
    elif len(not_found_in_spec) < 2:
      self.raiseAnError(NotImplementedError, f"A Component can only have one interaction! Check Component '{self.name}'")

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

  def get_crossrefs(self):
    """
    Collect the required value entities needed for this component to function.
    @ In, None
    @ Out, crossrefs, dict, mapping of dictionaries with information about the entities required.
    """
    crossrefs = {self._interaction: self._interaction.get_crossrefs()}
    crossrefs.update(self._economics.get_crossrefs())
    return crossrefs

  def set_crossrefs(self, refs):
    """
    Connect cross-reference material from other entities to the ValuedParams in this component.
    @ In, refs, dict, dictionary of entity information
    @ Out, None
    """
    try_match = self._interaction
    for interaction in list(refs.keys()):
      # find associated interaction
      if try_match == interaction:
        try_match.set_crossrefs(refs.pop(interaction))
        break
    # send what's left to the economics
    self._economics.set_crossrefs(refs)
    # if anything left, there's an issue
    assert not refs

  def get_interaction(self):
    """
    Return the interactions this component uses.
    @ In, None
    @ Out, interactions, list, list of Interaction instances
    """
    return self._interaction

  def get_sqrt_RTE(self):
    """
    Provide the square root of the round-trip efficiency for this component.
    Note we use the square root due to splitting loss across the input and output.
    @ In, None
    @ Out, RTE, float, round-trip efficiency as a multiplier
    """
    return self._interaction.get_sqrt_RTE()

  def print_me(self, tabs=0, tab="  "):
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    self.raiseADebug(pre + "Component:")
    self.raiseADebug(pre + "  name:", self.name)
    self._interaction.print_me(tabs=tabs + 1, tab=tab)

  def get_inputs(self):
    """
    returns list of all resources consumed here
    @ In, None
    @ Out, inputs, set, set of input resources as strings (resources that are taken/consumed/stored)
    """
    inputs = set()
    # simply combine the inputs for the interaction
    inputs.update(self._interaction.get_inputs())
    return inputs

  def get_outputs(self):
    """
    returns list of all resources producable here
    @ In, None
    @ Out, outputs, set, set of output resources as strings (resources that are produced/provided)
    """
    outputs = set()
    outputs.update(self._interaction.get_outputs())
    return outputs

  def get_resources(self):
    """
    Provides the full set of resources used by this component.
    @ In, None
    @ Out, res, set, set(str) of resource names
    """
    res = set()
    res.update(self.get_inputs())
    res.update(self.get_outputs())
    return res

  def get_capacity(self):
    """
    returns the capacity of the interaction of this component
    @ In, meta, dict, arbitrary metadata from EGRET
    @ In, raw, bool, optional, if True then return the ValuedParam instance for capacity, instead of the evaluation
    @ Out, capacity, float (or ValuedParam), the capacity of this component's interaction
    """
    return self._interaction.get_capacity()

  def get_minimum(self, meta, raw=False):
    """
    returns the minimum of the interaction of this component
    @ In, meta, dict, arbitrary metadata from EGRET
    @ In, raw, bool, optional, if True then return the ValuedParam instance for capacity, instead of the evaluation
    @ Out, capacity, float (or ValuedParam), the capacity of this component's interaction
    """
    return self._interaction.get_minimum(meta)

  def get_capacity_var(self):
    """
    Returns the variable that is used to define this component's capacity.
    @ In, None
    @ Out, var, str, name of capacity resource
    """
    return self._interaction.get_capacity_var()

  def get_tracking_vars(self) -> list[str]:
    """
    Provides the variables used by this component to track dispatch
    @ In, None
    @ Out, get_tracking_vars, list, variable name list
    """
    return self._interaction.get_tracking_vars()

  def is_dispatchable(self):
    """
    Returns the dispatchability indicator of this component.
    TODO Note that despite the name, this is NOT boolean, but a string indicator.
    @ In, None
    @ Out, dispatchable, str, dispatchability (e.g. independent, dependent, fixed)
    """
    return self._interaction.is_dispatchable()

  def is_governed(self) -> bool:
    """
    Determines if this component is optimizable or governed by some function.
    @ In, None
    @ Out, is_governed, bool, whether this component is governed.
    """
    return self._interaction.is_governed()

  def set_capacity(self, cap):
    """
    Set the float value of the capacity of this component's interaction
    @ In, cap, float, value
    @ Out, None
    """
    return self._interaction.set_capacity(cap)

  @property
  def ramp_limit(self):
    """
    Accessor for ramp limits on interactions.
    @ In, None
    @ Out, limit, float, limit
    """
    return self._interaction.ramp_limit

  @property
  def ramp_freq(self):
    """
    Accessor for ramp frequency limits on interactions.
    @ In, None
    @ Out, limit, float, limit
    """
    return self._interaction.ramp_freq

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

  def get_cashflows(self) -> list[CashFlow]:
    """
      Getter.
      @ In, None
      @ Out, cashflow, list, cash flows for this cashflow user (ordered)
    """
    return self._economics.get_cashflows()

  def get_state_cost(self, activity, meta, marginal=False):
    """
      get the cost given particular activities (state) of the cash flow user
      @ In, raven_vars, dict, additional variables (presumably from raven) that might be needed
      @ In, meta, dict, further dictionary of information that might be needed
      @ In, marginal, bool, optional, if True then only get marginal costs
      @ Out, cost, dict, cost of activity as a breakdown
    """
    return self._economics.evaluate_cfs(activity, meta, marginal=marginal)

  def get_economics(self) -> CashFlowGroup:
    """
      Accessor for economics.
      @ In, None
      @ Out, econ, CashFlowGroup, cash flows for this cash flow user
    """
    return self._economics
