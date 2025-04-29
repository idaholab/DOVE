# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import Any
from collections import defaultdict

from ravenframework.utils import InputData, InputTypes
from ravenframework.utils.InputData import ParameterInput

from ..physics import TransferFunc


class Interaction:
  """
  Base class for component interactions (e.g. Producer, Storage, Demand)
  """

  tag = "interacts"  # node name in input file

  @classmethod
  def get_input_specs(cls) -> type[ParameterInput]:
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    match cls.tag:
      case "produces":
        desc = r"indicates that this component produces one or more resources by consuming other resources."
        resource_desc = "the resource produced by this component's activity."
      case "stores":
        desc = "indicates that this component stores one resource, potentially absorbing or providing that resource."
        resource_desc = "the resource stored by this component."
      case "demands":
        desc = "indicates that this component exclusively consumes a resource."
        resource_desc = "the resource consumed by this component."
      case _:
        raise NotImplementedError(f"Class '{cls.tag}' not implemented!")

    specs = InputData.parameterInputFactory(cls.tag, ordered=False, descr=desc)
    specs.addParam(
      "resource",
      param_type=InputTypes.StringListType, # type: ignore
      required=True,
      descr=resource_desc,
    )

    specs.addParam(
      "dispatch",
      param_type=InputTypes.makeEnumType("dispatch_opts", "dispatch_opts", ["fixed", "independent", "dependent"]), # type: ignore
      required=True,
      descr=r"""describes the way this component should be dispatched, or its flexibility.
              \texttt{fixed} indicates the component always fully dispatched at
              its maximum level. \texttt{independent} indicates the component is
              fully dispatchable by the dispatch optimization algorithm.
              \texttt{dependent} indicates that while this component is not directly
              controllable by the dispatch algorithm, it can however be flexibly
              dispatched in response to other units changing dispatch level.
              For example, when attempting to increase profitability, the
              \texttt{fixed} components are not adjustable, but the \texttt{independent}
              components can be adjusted to attempt to improve the economic metric.
              In response to the \texttt{independent} component adjustment, the
              \texttt{dependent} components may respond to balance the resource
              usage from the changing behavior of other components.""",
    )


    cap = InputData.parameterInputFactory(
      "capacity",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""the maximum value at which this component can act, in units
                corresponding to the indicated resource. """
    )

    cap.addParam(
      "resource",
      param_type=InputTypes.StringType,
      descr=r"""indicates the resource that defines the capacity of this component's
              operation. For example, if a component consumes steam and electricity
              to produce hydrogen, the capacity of the component can be defined by
              the maximum steam consumable, maximum electricity consumable, or maximum
              hydrogen producable. Any choice should be nominally equivalent, but
              determines the units of the value of this node.""",
    )
    specs.addSub(cap)

    capfactor = InputData.parameterInputFactory(
      "capacity_factor",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""the actual value at which this component can act, as a unitless
                fraction of total rated capacity. Note that these factors are applied
                within the dispatch optimization; we assume that the capacity factor
                is not a variable in the outer optimization."""
    )
    specs.addSub(capfactor)

    minn = InputData.parameterInputFactory(
      "minimum",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""provides the minimum value at which this component can act, in
                units of the indicated resource."""
    )

    minn.addParam(
      "resource",
      param_type=InputTypes.StringType,
      descr=r"""indicates the resource that defines the minimum activity level for
                this component, as with the component's capacity.""",
    )
    specs.addSub(minn)

    return specs

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

  def get_transfer(self) -> None | TransferFunc:
    """
    Returns the transfer function, if any
    @ In, None
    @ Out, transfer, transfer ValuedParam
    """
    return self._transfer
