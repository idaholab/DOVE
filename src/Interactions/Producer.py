import numpy as np
from ravenframework.utils import InputData, InputTypes

from DOVE.src.Interactions import Interaction
from DOVE.src.TransferFuncs import factory as tf_factory


class Producer(Interaction):
  """
  Explains a particular interaction, where resources are consumed to produce other resources
  """

  tag = "produces"  # node name in input file

  @classmethod
  def get_input_specs(cls):
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    specs = super().get_input_specs()
    specs.addSub(
      InputData.parameterInputFactory(
        "consumes",
        contentType=InputTypes.StringListType,
        descr=r"""The producer can either produce or consume a resource.
                  If the producer is a consumer it must be accompanied with a transfer 
                  function to convert one source of energy to another.""",
      )
    )

    specs.addSub(
      tf_factory.make_input_specs(
        "transfer",
        descr=r"""describes the balance between consumed and produced resources 
                  for this component.""",
      )
    )
    specs.addSub(
      InputData.parameterInputFactory(
        "ramp_limit",
        contentType=InputTypes.FloatType,
        descr=r"""Limits the rate at which production can change between consecutive 
                  time steps, in either a positive or negative direction, as a 
                  percentage of this component's capacity. For example, a generator 
                  with a ramp limit of 0.10 cannot increase or decrease their
                  generation rate by more than 10 percent of capacity in a single 
                  time interval. \default{1.0}""",
      )
    )
    specs.addSub(
      InputData.parameterInputFactory(
        "ramp_freq",
        contentType=InputTypes.IntegerType,
        descr=r"""Places a limit on the number of time steps between successive production level
                      ramping events. For example, if time steps are an hour long and the ramp frequency
                      is set to 4, then once this component has changed production levels, 4 hours must
                      pass before another production change can occur. Note this limit introduces binary
                      variables and may require selection of appropriate solvers. \default{0}""",
      )
    )

    return specs

  def __init__(self, **kwargs):
    """
    Constructor
    @ In, None
    @ Out, None
    """
    Interaction.__init__(self, **kwargs)
    self._produces = []  # the resource(s) produced by this interaction
    self._consumes = []  # the resource(s) consumed by this interaction
    self._tracking_vars = ["production"]

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
    self._produces = specs.parameterValues["resource"]
    for item in specs.subparts:
      if item.getName() == "consumes":
        self._consumes = item.value
      elif item.getName() == "transfer":
        self._set_transfer_func("_transfer", comp_name, item)
      elif item.getName() == "ramp_limit":
        self.ramp_limit = item.value
      elif item.getName() == "ramp_freq":
        self.ramp_freq = item.value

    # input checking
    ## if a transfer function not given, can't be consuming a resource
    if self._transfer is None:
      if self._consumes:
        self.raiseAnError(
          IOError,
          "Any component that consumes a resource must have a transfer function describing the production process!",
        )
    ## transfer elements are all in IO list
    if self._transfer is not None:
      self._transfer.check_io(self.get_inputs(), self.get_outputs(), comp_name)
      self._transfer.set_io_signs(self.get_inputs(), self.get_outputs())
    ## ramp limit is (0, 1]
    if self.ramp_limit is not None and not 0 < self.ramp_limit <= 1:
      self.raiseAnError(
        IOError, f'Ramp limit must be (0, 1] but got "{self.ramp_limit}"'
      )

  def _set_transfer_func(self, name, comp, spec):
    """
    Sets up a Transfer Function
    @ In, name, str, name of member of this class
    @ In, comp, str, name of associated component
    @ In, spec, inputparam, input specifications
    @ Out, None
    """
    known = tf_factory.knownTypes()
    found = False
    for sub in spec.subparts:
      if sub.getName() in known:
        if found:
          self.raiseAnError(
            IOError, f'Received multiple Transfer Functions for component "{name}"!'
          )
        self._transfer = tf_factory.returnInstance(sub.getName())
        self._transfer.read(comp, spec)
        found = True

  def get_inputs(self):
    """
    Returns the set of resources that are inputs to this interaction.
    @ In, None
    @ Out, inputs, set, set of inputs
    """
    inputs = Interaction.get_inputs(self)
    inputs.update(np.atleast_1d(self._consumes))
    return inputs

  def get_outputs(self):
    """
    Returns the set of resources that are outputs to this interaction.
    @ In, None
    @ Out, outputs, set, set of outputs
    """
    outputs = set(np.atleast_1d(self._produces))
    return outputs

  def print_me(self, tabs: int = 0, tab: str = "  ") -> None:
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    self.raiseADebug(pre + "Producer:")
    self.raiseADebug(pre + "  produces:", self._produces)
    self.raiseADebug(pre + "  consumes:", self._consumes)
    self.raiseADebug(pre + "  transfer:", self._transfer)
    self.raiseADebug(pre + "  capacity:", self._capacity)
