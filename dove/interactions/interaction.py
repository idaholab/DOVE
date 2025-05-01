# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from collections import defaultdict
from typing import Any

from ravenframework.utils import InputData, InputTypes
from ravenframework.utils.InputData import ParameterInput


class Interaction:
  """
  Base class for component interactions (e.g. Producer, Storage, Demand)
  """

  tag = "interacts"  # node name in input file

  def __init__(self, **kwargs) -> None:
    """
    Constructor
    @ In, kwargs, dict, arbitrary pass-through arguments
    @ Out, None
    """
    self._capacity = None  # upper limit of this interaction
    self._capacity_factor = None  # ratio of actual output as fraction of _capacity
    self._signals = set()  # dependent signals for this interaction
    self._crossrefs: defaultdict[str, Any] = defaultdict(dict)  # crossrefs objects needed (e.g. armas, etc), as {attr: {tag, name, obj})
    self._minimum = None  # lowest interaction level, if dispatchable
    self._minimum_var = None  # limiting variable for minimum
    self._transfer = None  # the production rate (if any), in produces per consumes
    self.dispatch_flexibility = "independent"
    self.capacity_var = None  # which variable limits the capacity (could be produced or consumed?)
    self.tracking_vars: list[str] = []  # list of trackable variables for dispatch activity
    self.inputs: set[str] = set()
    self.outputs: set[str] = set()

  def _set_fixed_value(self, name: str, value: float) -> None:
    """
    """
    setattr(self, name, value)

  def _set_value(self, name: str, comp_name: str, spec: InputData.ParameterInput) -> None:
    """
    """
    setattr(self, name, spec.value)

  def read_input(self, specs: InputData.ParameterInput, comp_name: str) -> None:
    """
    Sets settings from input file
    @ In, specs, InputData.ParameterInput, defined input specification
    @ In, comp_name, str, name of component this Interaction belongs to
    @ Out, None
    """
    self.dispatch_flexibility = specs.parameterValues["dispatch"]
    self.capacity_var = specs.parameterValues["resource"][0]

    for item in specs.subparts:
      match (item_name := item.getName()):
        case "capacity_factor":
          self._set_value(f"_{item_name}", comp_name, item)
        case "capacity":
          self.capacity_var = item.parameterValues.get("resource", self.capacity_var)
          self._set_value(f"_{item_name}", comp_name, item)
        case "minimum":
          self._minimum_var = item.parameterValues.get("resource", self.capacity_var)
          self._set_value(f"_{item_name}", comp_name, item)

    # finalize some values
    resources = set(list(self.inputs) + list(self.outputs))

    ## capacity: if "variable" is None and only one resource in interactions, then that must be it
    if self.capacity_var is None:
      if len(resources) == 1:
        self.capacity_var = list(resources)[0]
      else:
        raise IOError(f'Component "{comp_name}": If multiple resources are active, "capacity" requires a "resource" specified!')

    ## minimum: basically the same as capacity, functionally
    if self._minimum and self._minimum_var is None:
      if len(resources) == 1:
        self._minimum_var = list(resources)[0]
      else:
        raise IOError(f'Component "{comp_name}": If multiple resources are active, "minimum" requires a "resource" specified!')

  @property
  def resources(self) -> set[str]:
    """
    """
    res: set[str] = set()
    res.update(self.inputs)
    res.update(self.outputs)
    return res

  def is_governed(self) -> bool:
    """
    Determines if this interaction is optimizable or governed by some function.
    @ In, None
    @ Out, is_governed, bool, whether this component is governed.
    """
    return False
