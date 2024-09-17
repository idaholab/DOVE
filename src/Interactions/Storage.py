import numpy as np
from ravenframework.utils import InputData, InputTypes

from DOVE.src.Interactions import Interaction


class Storage(Interaction):
  """
  Explains a particular interaction, where a resource is stored and released later
  """

  tag = "stores"  # node name in input file

  @classmethod
  def get_input_specs(cls):
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    specs = super().get_input_specs()
    # TODO unused, please implement ... :
    # descr = r"""the limiting charge/discharge rate of this storage. """
    # specs.addSub(ValuedParam.get_input_specs('rate'))
    # initial stored
    descr = r"""indicates what percent of the storage unit is full at the start of each optimization sequence,
              from 0 to 1. \default{0.0}. """
    sub = InputData.parameterInputFactory(
      "initial_stored", contentType=InputTypes.FloatOrIntType, descr=descr
    )  # vp_factory.make_input_specs('initial_stored', descr=descr)
    specs.addSub(sub)

    # periodic level boundary condition
    descr = r"""indicates whether the level of the storage should be required to return to its initial level
              within each modeling window. If True, this reduces the flexibility of the storage, but if False,
              can result in breaking conservation of resources. \default{True}. """
    sub = InputData.parameterInputFactory(
      "periodic_level", contentType=InputTypes.BoolType, descr=descr
    )
    specs.addSub(sub)

    # control strategy
    # descr=r"""control strategy for operating the storage. If not specified, uses a perfect foresight strategy. """
    # specs.addSub(vp_factory.make_input_specs('strategy', allowed=['Function'], descr=descr))
    # round trip efficiency
    descr = r"""round-trip efficiency for this component as a scalar multiplier. \default{1.0}"""
    specs.addSub(
      InputData.parameterInputFactory(
        "RTE", contentType=InputTypes.FloatType, descr=descr
      )
    )
    return specs

  def __init__(self, **kwargs):
    """
    Constructor
    @ In, kwargs, dict, passthrough args
    @ Out, None
    """
    Interaction.__init__(self, **kwargs)
    self.apply_periodic_level = (
      True  # whether to apply periodic boundary conditions for the level of the storage
    )
    self._stores = None  # the resource stored by this interaction
    self._rate = None  # the rate at which this component can store up or discharge
    self._initial_stored = (
      None  # how much resource does this component start with stored?
    )
    self._strategy = None  # how to operate storage unit
    self._tracking_vars = [
      "level",
      "charge",
      "discharge",
    ]  # stored quantity, charge activity, discharge activity

  def read_input(self, specs, comp_name):
    """
    Sets settings from input file
    @ In, specs, InputData, specs
    @ In, mode, string, case mode to operate in (e.g. 'sweep' or 'opt')
    @ In, comp_name, string, name of component this Interaction belongs to
    @ Out, None
    """
    # specs were already checked in Component
    Interaction.read_input(self, specs, comp_name)
    self._stores = specs.parameterValues["resource"]
    for item in specs.subparts:
      if item.getName() == "rate":
        # self._set_valued_param('_rate', comp_name, item, mode)
        pass
      elif item.getName() == "initial_stored":
        # self._set_valued_param('_initial_stored', comp_name, item, mode)
        pass
      elif item.getName() == "periodic_level":
        self.apply_periodic_level = item.value
      elif item.getName() == "strategy":
        # self._set_valued_param('_strategy', comp_name, item, mode)
        pass
      elif item.getName() == "RTE":
        self._sqrt_rte = np.sqrt(item.value)
    assert (
      len(self._stores) == 1
    ), f'Multiple storage resources given for component "{comp_name}"'
    self._stores = self._stores[0]
    # checks and defaults
    if self._initial_stored is None:
      self.raiseAWarning(
        f'Initial storage level for "{comp_name}" was not provided! Defaulting to 0%.'
      )
      # make a fake reader node for a 0 value
      # vp = ValuedParamHandler('initial_stored')
      # vp.set_const_VP(0.0)
      # self._initial_stored = vp
    # the capacity is limited by the stored resource.
    self._capacity_var = self._stores

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

  def is_governed(self):
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
    self.raiseADebug(pre + "  rate:", self._rate)
    self.raiseADebug(pre + "  capacity:", self._capacity)

  def _check_capacity_limit(
    self, res, amt, balance, meta, raven_vars, dispatch, t, level
  ):
    """
    Check to see if capacity limits of this component have been violated.
    overloads Interaction method, since units for storage are "res" not "res per second"
    @ In, res, str, name of capacity-limiting resource
    @ In, amt, float, requested amount of resource used in interaction
    @ In, balance, dict, results of requested interaction
    @ In, meta, dict, additional variable passthrough
    @ In, raven_vars, dict, TODO part of meta! consolidate!
    @ In, dispatch, dict, TODO part of meta! consolidate!
    @ In, t, int, TODO part of meta! consolidate!
    @ In, level, float, current level of storage
    @ Out, balance, dict, new results of requested action, possibly modified if capacity hit
    @ Out, meta, dict, additional variable passthrough
    """
    # note "amt" has units of AMOUNT not RATE (resource, not resource per second)
    sign = np.sign(amt)
    # are we storing or providing?
    # print('DEBUGG supposed current level:', level)
    if sign < 0:
      # we are being asked to consume some
      cap, meta = self.get_capacity(meta, raven_vars, dispatch, t)
      available_amount = cap[res] - level
      # print('Supposed Capacity, Only calculated ins sign<0 (being asked to consumer)',cap)
    else:
      # we are being asked to produce some
      available_amount = level
    # the amount we can consume is the minimum of the requested or what's available
    delta = sign * min(available_amount, abs(amt))
    return {res: delta}, meta

  def _check_rate_limit(self, res, amt, balance, meta, raven_vars, dispatch, t):
    """
    Determines the limiting rate of in/out production for storage
    @ In, res, str, name of capacity-limiting resource
    @ In, amt, float, requested amount of resource used in interaction
    @ In, balance, dict, results of requested interaction
    @ In, meta, dict, additional variable passthrough
    @ In, raven_vars, dict, TODO part of meta! consolidate!
    @ In, dispatch, dict, TODO part of meta! consolidate!
    @ In, t, int, TODO part of meta! consolidate!
    @ Out, balance, dict, new results of requested action, possibly modified if capacity hit
    @ Out, meta, dict, additional variable passthrough
    """
    # TODO distinct up/down rates
    # check limiting rate for resource flow in/out, if any
    if self._rate:
      request = {res: None}
      inputs = {
        "request": request,
        "meta": meta,
        "raven_vars": raven_vars,
        "dispatch": dispatch,
        "t": t,
      }
      max_rate = self._rate.evaluate(inputs, target_var=res)[0][res]
      delta = np.sign(amt) * min(max_rate, abs(amt))
      print(
        "max_rate in _check_rate_limit",
        max_rate,
        "delta (min of maxrate and abs(amt)",
        delta,
      )
      return {res: delta}, meta
    return {res: amt}, meta

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
