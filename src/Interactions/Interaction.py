""" """
from collections import defaultdict

from DOVE.src.Base import Base

from ravenframework.utils import InputData, InputTypes
from ravenframework.utils.InputData import ParameterInput

class Interaction(Base):
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
    if cls.tag == "produces":
      desc = r"""indicates that this component produces one or more resources by
                 consuming other resources."""
      resource_desc = r"""the resource produced by this component's activity."""

    elif cls.tag == "stores":
      desc = r"""indicates that this component stores one resource, potentially
                 absorbing or providing that resource."""
      resource_desc = r"""the resource stored by this component."""

    elif cls.tag == "demands":
      desc = r"""indicates that this component exclusively consumes a resource."""
      resource_desc = r"""the resource consumed by this component."""

    specs = InputData.parameterInputFactory(cls.tag, ordered=False, descr=desc)
    specs.addParam(
      "resource",
      param_type=InputTypes.StringListType,
      required=True,
      descr=resource_desc,
    )

    specs.addParam(
      "dispatch",
      param_type=InputTypes.makeEnumType("dispatch_opts", "dispatch_opts", ["fixed", "independent", "dependent"]),
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
    Base.__init__(self, **kwargs)
    self._capacity = None  # upper limit of this interaction
    self._capacity_var = None  # which variable limits the capacity (could be produced or consumed?)
    self._capacity_factor = None  # ratio of actual output as fraction of _capacity
    self._signals = set()  # dependent signals for this interaction
    self._crossrefs = defaultdict(dict)  # crossrefs objects needed (e.g. armas, etc), as {attr: {tag, name, obj})
    self._dispatchable = "independent"  # independent, dependent, or fixed?
    self._minimum = None  # lowest interaction level, if dispatchable
    self._minimum_var = None  # limiting variable for minimum
    self.ramp_limit = None  # limiting change of production in a time step
    self.ramp_freq = None  # time steps required between production ramping events
    self._transfer = None  # the production rate (if any), in produces per consumes
    self._tracking_vars: list[str] = []  # list of trackable variables for dispatch activity

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
    @ In, specs, InputData, specs
    @ In, mode, string, case mode to operate in (e.g. 'sweep' or 'opt')
    @ In, comp_name, string, name of component this Interaction belongs to
    @ Out, None
    """
    self.raiseADebug(f' ... loading interaction "{self.tag}"')
    self._dispatchable = specs.parameterValues["dispatch"]
    self._capacity_var = specs.parameterValues["resource"][0]

    for item in specs.subparts:
      match (item_name := item.getName()):
        case "capacity_factor":
          self._set_value(f"_{item_name}", comp_name, item)
        case "capacity":
          self._capacity_var = item.parameterValues.get("resource", self._capacity_var)
          self._set_value(f"_{item_name}", comp_name, item)
        case "minimum":
          self._minimum_var = item.parameterValues.get("resource", self._capacity_var)
          self._set_value(f"_{item_name}", comp_name, item)

    # finalize some values
    resources = set(list(self.get_inputs()) + list(self.get_outputs()))

    ## capacity: if "variable" is None and only one resource in interactions, then that must be it
    if self._capacity_var is None:
      print(len(resources))
      if len(resources) == 1:
        self._capacity_var = list(resources)[0]
      else:
        self.raiseAnError(IOError,f'Component "{comp_name}": If multiple resources are active, "capacity" requires a "resource" specified!')

    ## minimum: basically the same as capacity, functionally
    if self._minimum and self._minimum_var is None:
      if len(resources) == 1:
        self._minimum_var = list(resources)[0]
      else:
        self.raiseAnError(IOError, f'Component "{comp_name}": If multiple resources are active, "minimum" requires a "resource" specified!')

  def get_capacity(self):
    """
    Returns the capacity of this interaction.
    Returns an evaluated value unless "raw" is True, then gives ValuedParam
    @ In, meta, dict, additional variables to pass through
    @ In, raw, bool, optional, if True then provide ValuedParam instead of evaluation
    @ Out, evaluated, float or ValuedParam, requested value
    @ Out, meta, dict, additional variable passthrough
    """
    if self._capacity_factor is None:
      return self._capacity
    return self._capacity * self._capacity_factor

  def get_capacity_var(self) -> str:
    """
    Returns the resource variable that is used to define the capacity limits of this interaction.
    @ In, None
    @ Out, capacity_var, string, name of capacity-limiting resource
    """
    return self._capacity_var

  def set_capacity(self, cap):
    """
    Allows hard-setting the capacity of this interaction.
    This destroys any underlying ValuedParam that was there before.
    @ In, cap, float, capacity value
    @ Out, None
    """
    self._capacity.set_value(float(cap))

  def get_minimum(self, meta):
    """
    Returns the minimum level of this interaction.
    Returns an evaluated value unless "raw" is True, then gives ValuedParam
    @ In, meta, dict, additional variables to pass through
    @ In, raw, bool, optional, if True then provide ValuedParam instead of evaluation
    @ Out, evaluated, float or ValuedParam, requested value
    @ Out, meta, dict, additional variable passthrough
    """
    return self._minimum

  def get_crossrefs(self):
    """
    Getter.
    @ In, None
    @ Out, crossrefs, dict, resource references
    """
    return self._crossrefs

  def set_crossrefs(self, refs) -> None:
    """
    Setter.
    @ In, refs, dict, resource cross-reference objects
    @ Out, None
    """
    # connect references to ValuedParams (Placeholder objects)
    for attr, obj in refs.items():
      valued_param = self._crossrefs[attr]
      valued_param.set_object(obj)
    # perform crosscheck that VPs have what they need
    for attr, vp in self.get_crossrefs().items():
      vp.crosscheck(self)

  def get_inputs(self) -> set[str]:
    """
    Returns the set of resources that are inputs to this interaction.
    @ In, None
    @ Out, inputs, set, set of inputs
    """
    return set()

  def get_outputs(self) -> set[str]:
    """
    Returns the set of resources that are outputs to this interaction.
    @ In, None
    @ Out, outputs, set, set of outputs
    """
    return set()

  def get_resources(self) -> list[str]:
    """
    Returns set of resources used by this interaction.
    @ In, None
    @ Out, resources, set, set of resources
    """
    return list(self.get_inputs()) + list(self.get_outputs())

  def get_tracking_vars(self) -> list[str]:
    """
    Provides the variables used by this component to track dispatch
    @ In, None
    @ Out, get_tracking_vars, list, variable name list
    """
    return self._tracking_vars

  def is_dispatchable(self) -> str:
    """
    Getter. Indicates if this interaction is Fixed, Dependent, or Independent.
    @ In, None
    @ Out, dispatchable, string, one of 'fixed', 'dependent', or 'independent'
    """
    return self._dispatchable

  def is_type(self, typ: str) -> bool:
    """
    Checks if this interaction matches the request.
    @ In, typ, string, name to check against
    @ Out, is_type, bool, whether there is a match or not.
    """
    return typ == self.__class__.__name__

  def is_governed(self) -> bool:
    """
    Determines if this interaction is optimizable or governed by some function.
    @ In, None
    @ Out, is_governed, bool, whether this component is governed.
    """
    return False

  def get_transfer(self):
    """
    Returns the transfer function, if any
    @ In, None
    @ Out, transfer, transfer ValuedParam
    """
    return self._transfer
