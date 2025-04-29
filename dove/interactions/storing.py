# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Storage Interaction Module
"""
import math
import warnings

from ravenframework.utils import InputData, InputTypes
from ravenframework.utils.InputData import ParameterInput

from . import Interaction

class Storage(Interaction):
  """
  Explains a particular interaction, where a resource is stored and released later
  """

  tag = "stores"  # node name in input file

  @classmethod
  def get_input_specs(cls) -> type[ParameterInput]:
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    specs = super().get_input_specs()

    specs.addParam(
      "periodic_level",
      param_type=InputTypes.BoolType, # type: ignore
      required=False,
      default="True",
      descr=r"""indicates whether the level of the storage should be required to
                return to its initial level within each modeling window. If True,
                this reduces the flexibility of the storage, but if False, can
                result in breaking conservation of resources. \default{True}."""
    )

    specs.addParam(
      "rte",
      param_type=InputTypes.FloatType, # type: ignore
      required=False,
      default="1.0",
      descr=r"""round-trip efficiency for this component as a scalar multiplier. \default{1.0}"""
    )

    specs.addSub(InputData.parameterInputFactory(
      "initial_stored",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""indicates what percent of the storage unit is full at the start
                of each optimization sequence, from 0 to 1. \default{0.0}."""
    ))

    # TODO: Need to revisit strategy param for DOVE since no functions are expected.
    specs.addSub(InputData.parameterInputFactory(
      "strategy",
      contentType=InputTypes.StringType,
      descr=r"""control strategy for operating the storage. If not specified,
                uses a perfect foresight strategy. """
    ))

    return specs

  def __init__(self, **kwargs) -> None:
    """
    Constructor
    @ In, kwargs, dict, passthrough args
    @ Out, None
    """
    Interaction.__init__(self, **kwargs)
    self._initial_stored = None  # how much resource does this component start with stored?
    self._strategy = None  # how to operate storage unit
    self.tracking_vars = ["level", "charge", "discharge",]
    self.sqrt_rte = 1.0
    self.apply_periodic_level = True

  def read_input(self, specs, comp_name: str) -> None:
    """
    Sets settings from input file
    @ In, specs, InputData, specs
    @ In, mode, string, case mode to operate in (e.g. 'sweep' or 'opt')
    @ In, comp_name, string, name of component this Interaction belongs to
    @ Out, None
    """
    # specs were already checked in Component
    Interaction.read_input(self, specs, comp_name)
    self.inputs = self.outputs = set(specs.parameterValues["resource"])
    self.apply_periodic_level = specs.parameterValues.get("periodic_level", self.apply_periodic_level)
    self.sqrt_rte = math.sqrt(specs.parameterValues.get("rte", self.sqrt_rte))

    for item in specs.subparts:
      match (name := item.getName()):
        case "initial_stored" | "strategy":
          self._set_value(f"_{name}", comp_name, item)

    if self._initial_stored is None:
      warnings.warn(f'Initial storage level for "{comp_name}" was not provided! Defaulting to 0%.')
      self._set_fixed_value('_initial_stored', 0.0)

  def get_stored_resource(self) -> str:
    """
    Returns the resource this unit stores.
    @ In, None
    @ Out, stores, str, resource stored
    """
    return list(self.inputs)[0]

  def get_strategy(self):
    """
    Returns the resource this unit stores.
    @ In, None
    @ Out, stores, str, resource stored
    """
    return self._strategy

  def is_governed(self) -> bool:
    """
    Determines if this interaction is optimizable or governed by some function.
    @ In, None
    @ Out, is_governed, bool, whether this component is governed.
    """
    return self._strategy is not None

  def print_me(self, tabs=0, tab="  "):
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    print(pre + "Storage:")
    print(pre + "  stores:", self.inputs)
    print(pre + "  capacity:", self._capacity)
