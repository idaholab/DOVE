# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Module
"""
from dataclasses import dataclass, field, InitVar
from abc import ABC
from collections import defaultdict
from typing import Literal, Optional, NewType, Any

ResourceName = NewType("ResourceName", str)
DispatchFlex = Literal["fixed", "independent"]
CashFlowKind = Literal["one-time", "repeating"]
CashFlowPeriod = Literal["hour", "year"]

@dataclass(frozen=True)
class ResourceSpec:
  """ """
  name: ResourceName
  unit: Optional[str] = None

@dataclass
class CashFlow:
  """ """
  name: str
  driver: float
  reference_price: float
  reference_driver: float =  1.0
  scaling_factor_x: float =  1.0
  depreciation: int | None = None
  has_inflation: bool = False
  is_npv_exempt: bool = False
  is_price_levelized: bool = False
  is_taxable: bool = True
  period: CashFlowPeriod = "year"
  category: CashFlowKind = "repeating"
  signals: set = field(default_factory=set)
  crossrefs: defaultdict[str, Any] = field(default_factory=lambda: defaultdict(dict))


@dataclass(kw_only=True)
class Component(ABC):
  """
  Represents a system component in the grid analysis. Each component has a
  single "interaction" that describes what it can do (produce, store, demand)
  and a single CashFlowGroup which is a container for component associated cashflows.
  """
  name: str
  lifetime: int
  capacity: float
  capacity_var: ResourceSpec
  capacity_factor: float | None = None
  minimum: float | None = None
  dispatch_flexibility: DispatchFlex = "independent"
  cashflows: list[CashFlow] = field(default_factory=list)
  levelized_meta: dict = field(default_factory=dict)

@dataclass
class Producer(Component):
  """ """
  produces: ResourceSpec
  transfer: Any = None
  ramp_limit: float = 1.0
  ramp_freq: float = 0
  consumes: list[ResourceSpec] = field(default_factory=list)
  tracking_vars: list[str] = field(default_factory=lambda: ["production"])


@dataclass
class Storage(Component):
  """ """
  consumes: ResourceSpec
  produces: ResourceSpec
  rte: float = 1.0
  max_charge_rate: float = 1.0
  max_discharge_rate: float = 1.0
  initial_stored: float = 0
  periodic_level: bool = True
  tracking_vars: list[str] = field(default_factory=lambda: ["level", "charge", "discharge",])

@dataclass
class Demand(Component):
  """ """
  consumes: ResourceSpec
  tracking_vars: list[str] = field(default_factory=lambda: ["production"])

  # def read_input(self, xml: ET.Element) -> None:
  #   """
  #   Sets settings from input file
  #   @ In, xml, xml.etree.ElementTree.Element, component information from xml input file.
  #   @ Out, None
  #   """
  #   specs = self.get_input_specs()()
  #   specs.parseNode(xml)
  #   interaction_map = {"produces": Producer, "stores": Storage, "demands": Demand}
  #   self.assign_attrs_from_specs(specs, interaction_map, CashFlowGroup)

  # def assign_attrs_from_specs(
  #     self,
  #     specs: InputData.ParameterInput,
  #     interaction_map: dict[str, type[Demand | Storage | Producer]],
  #     cfg_type: type[CashFlowGroup]
  # ) -> None:
  #   """
  #   Sets class attributes and children nodes based on the type of Interaction and CashFlowGroup
  #   @ In, specs, Input.Data.ParameterInput, filled-out input specification.
  #   @ In, interaction_map, dict[str, Interaction], dictionary mapping cls.tag to proper class.
  #   @ In, cfg_type, CashFlowGroup, a kind of cashflowgroup (i.e. VP or List)
  #   @ Out, None
  #   """
  #   self.name = specs.parameterValues["name"]

  #   found_interactions, not_found_in_spec = specs.findNodesAndExtractValues(interaction_map.keys())
  #   if all((interaction == 'no-default' for interaction in found_interactions.values())):
  #     raise ComponentError(f"No interaction found for Component '{self.name}'!")
  #   elif len(not_found_in_spec) < 2: # Three allowed -- if less than two not found, we have a problem.
  #     raise ComponentError(f"A Component can only have one interaction! Check Component '{self.name}'")

  #   for item in specs.subparts:
  #     item_name = item.getName()
  #     if item_name in interaction_map:
  #       interaction_instance = interaction_map[item_name]()
  #       interaction_instance.read_input(item, self.name)
  #       self._interaction = interaction_instance
  #     elif item_name == 'economics':
  #       cashflows = cfg_type(self)
  #       cashflows.read_input(item)
  #       self._economics = cashflows

  # @property
  # def interaction(self) -> Demand | Producer | Storage:
  #   """
  #   Returns private member `_interaction` after making sure it's been set.
  #   @ In, None
  #   @ Out, interaction, type[Interaction]
  #   """
  #   if self._interaction is None:
  #     raise AttributeError(f"component '{self.name}' has no attribute 'interaction'!")
  #   return self._interaction

  # @property
  # def economics(self) -> CashFlowGroup:
  #   """
  #   Returns private member `_economics` after making sure it's been set.
  #   @ In, None
  #   @ Out, economics, type[CashFlowGroup]
  #   """
  #   if self._economics is None:
  #     raise AttributeError(f"component '{self.name}' has no attribute 'economics'!")
  #   return self._economics

  # def print_me(self, tabs=0, tab="  ") -> None:
  #   """
  #   Prints info about self
  #   @ In, tabs, int, optional, number of tabs to insert before prints
  #   @ In, tab, str, optional, characters to use to denote hierarchy
  #   @ Out, None
  #   """
  #   pre = tab * tabs
  #   print(pre + "Component:")
  #   print(pre + "  name:", self.name)
  #   self.interaction.print_me(tabs=tabs + 1, tab=tab)

