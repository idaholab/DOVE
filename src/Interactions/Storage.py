# Copyright 2020, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Storage Interaction Module
"""
import numpy as np

from DOVE.src.Interactions import Interaction

from ravenframework.utils import InputData, InputTypes
from ravenframework.utils.InputData import ParameterInput

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

    specs.addSub(InputData.parameterInputFactory(
      "initial_stored",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""indicates what percent of the storage unit is full at the start
                of each optimization sequence, from 0 to 1. \default{0.0}."""
    ))

    specs.addSub(InputData.parameterInputFactory(
      "periodic_level",
      contentType=InputTypes.BoolType,
      descr=r"""indicates whether the level of the storage should be required to
                return to its initial level within each modeling window. If True,
                this reduces the flexibility of the storage, but if False, can
                result in breaking conservation of resources. \default{True}."""
    ))

    # TODO: Need to revisit strategy param for DOVE since no functions are expected.
    specs.addSub(InputData.parameterInputFactory(
      "strategy",
      contentType=InputTypes.StringType,
      descr=r"""control strategy for operating the storage. If not specified,
                uses a perfect foresight strategy. """
    ))

    specs.addSub(InputData.parameterInputFactory(
      "RTE",
      contentType=InputTypes.FloatType,
      descr=r"""round-trip efficiency for this component as a scalar multiplier. \default{1.0}"""
    ))

    return specs

  def __init__(self, **kwargs):
    """
    Constructor
    @ In, kwargs, dict, passthrough args
    @ Out, None
    """
    Interaction.__init__(self, **kwargs)
    self.apply_periodic_level = True  # whether to apply periodic boundary conditions for the level of the storage
    self._stores: str = ""  # the resource stored by this interaction
    self._initial_stored = None  # how much resource does this component start with stored?
    self._strategy = None  # how to operate storage unit
    self._tracking_vars = ["level", "charge", "discharge",]  # stored quantity, charge activity, discharge activity
    self._sqrt_rte = 1.0

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
    self._stores = specs.parameterValues["resource"][0]

    for item in specs.subparts:
      item_name = item.getName()
      if item_name == "initial_stored":
        self._set_value('_initial_stored', comp_name, item)
      elif item_name == "strategy":
        self._set_value('_strategy', comp_name, item)
      elif item_name == "periodic_level":
        self.apply_periodic_level = item.value
      elif item_name == "RTE":
        self._sqrt_rte = np.sqrt(item.value)

    if self._initial_stored is None:
      self.raiseAWarning(f'Initial storage level for "{comp_name}" was not provided! Defaulting to 0%.')
      self._set_fixed_value('_initial_stored', 0.0)

  def get_sqrt_RTE(self):
    """
    Provide the square root of the round-trip efficiency for this component.
    Note we use the square root due to splitting loss across the input and output.
    @ In, None
    @ Out, RTE, float, round-trip efficiency as a multiplier
    """
    return self._sqrt_rte

  def get_inputs(self):
    """
    Returns the set of resources that are inputs to this interaction.
    @ In, None
    @ Out, inputs, set, set of inputs
    """
    inputs = Interaction.get_inputs(self)
    inputs.update(np.atleast_1d(self._stores))
    return inputs

  def get_outputs(self):
    """
    Returns the set of resources that are outputs to this interaction.
    @ In, None
    @ Out, outputs, set, set of outputs
    """
    outputs = Interaction.get_outputs(self)
    outputs.update(np.atleast_1d(self._stores))
    return outputs

  def get_resource(self):
    """
    Returns the resource this unit stores.
    @ In, None
    @ Out, stores, str, resource stored
    """
    return self._stores

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
    self.raiseADebug(pre + "Storage:")
    self.raiseADebug(pre + "  stores:", self._stores)
    #self.raiseADebug(pre + "  rate:", self._rate)
    self.raiseADebug(pre + "  capacity:", self._capacity)

  def get_initial_level(self, meta):
    """
    Find initial level of the storage
    @ In, meta, dict, additional variable passthrough
    @ Out, initial, float, initial level
    """
    res = self.get_resource()
    request = {res: None}
    meta["request"] = request
    pct = self._initial_stored.evaluate(meta, target_var=res)[0][res]
    if not (0 <= pct <= 1):
      self.raiseAnError(
        ValueError,
        f'While calculating initial storage level for storage "{self.tag}", '
        + f"an invalid percent was provided/calculated ({pct}). Initial levels should be between 0 and 1, inclusive.",
      )
    amt = pct * self.get_capacity(meta)[0][res]
    return amt
