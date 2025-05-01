# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Module
"""
import xml.etree.ElementTree as ET

from ravenframework.utils import InputData, InputTypes

from .economics import CashFlowGroup
from .interactions import Demand, Producer, Storage

class ComponentError(Exception):
  """
  Custom exception for component errors.
  """
  pass

class Component:
  """
  Represents a system component in the grid analysis. Each component has a
  single "interaction" that describes what it can do (produce, store, demand)
  and a single CashFlowGroup which is a container for component associated cashflows.
  """

  def __init__(self, **kwargs) -> None:
    """
    Constructor
    @ In, kwargs, dict, optional, arguments to pass to other constructors
    @ Out, None
    """
    self.name = "placeholder" # Name is required, so just initialize with a temp name.
    self.levelized_meta = {}
    self._interaction = None
    self._economics = None

  def __repr__(self) -> str:
    """
    String representation.
    @ In, None
    @ Out, __repr__, string representation
    """
    return f'<DOVE Component "{self.name}">'

  def read_input(self, xml: ET.Element) -> None:
    """
    Sets settings from input file
    @ In, xml, xml.etree.ElementTree.Element, component information from xml input file.
    @ Out, None
    """
    specs = self.get_input_specs()()
    specs.parseNode(xml)
    interaction_map = {"produces": Producer, "stores": Storage, "demands": Demand}
    self.assign_attrs_from_specs(specs, interaction_map, CashFlowGroup)

  def assign_attrs_from_specs(
      self,
      specs: InputData.ParameterInput,
      interaction_map: dict[str, type[Demand | Storage | Producer]],
      cfg_type: type[CashFlowGroup]
  ) -> None:
    """
    Sets class attributes and children nodes based on the type of Interaction and CashFlowGroup
    @ In, specs, Input.Data.ParameterInput, filled-out input specification.
    @ In, interaction_map, dict[str, Interaction], dictionary mapping cls.tag to proper class.
    @ In, cfg_type, CashFlowGroup, a kind of cashflowgroup (i.e. VP or List)
    @ Out, None
    """
    self.name = specs.parameterValues["name"]

    found_interactions, not_found_in_spec = specs.findNodesAndExtractValues(interaction_map.keys())
    if all((interaction == 'no-default' for interaction in found_interactions.values())):
      raise ComponentError(f"No interaction found for Component '{self.name}'!")
    elif len(not_found_in_spec) < 2: # Three allowed -- if less than two not found, we have a problem.
      raise ComponentError(f"A Component can only have one interaction! Check Component '{self.name}'")

    for item in specs.subparts:
      item_name = item.getName()
      if item_name in interaction_map:
        interaction_instance = interaction_map[item_name]()
        interaction_instance.read_input(item, self.name)
        self._interaction = interaction_instance
      elif item_name == 'economics':
        cashflows = cfg_type(self)
        cashflows.read_input(item)
        self._economics = cashflows

  @property
  def interaction(self) -> Demand | Producer | Storage:
    """
    Returns private member `_interaction` after making sure it's been set.
    @ In, None
    @ Out, interaction, type[Interaction]
    """
    if self._interaction is None:
      raise AttributeError(f"component '{self.name}' has no attribute 'interaction'!")
    return self._interaction

  @property
  def economics(self) -> CashFlowGroup:
    """
    Returns private member `_economics` after making sure it's been set.
    @ In, None
    @ Out, economics, type[CashFlowGroup]
    """
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
    print(pre + "Component:")
    print(pre + "  name:", self.name)
    self.interaction.print_me(tabs=tabs + 1, tab=tab)

