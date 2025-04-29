# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Producer interaction module
"""

from ravenframework.utils import InputData, InputTypes

from ..physics import TransferFunc
from ..physics import factory as tf_factory
from . import Interaction


class ProducerError(Exception):
  """
  """
  pass


class Producer(Interaction):
  """
  Explains a particular interaction, where resources are consumed to produce other resources
  """

  tag = "produces"  # node name in input file

  @classmethod
  def get_input_specs(cls) -> type[InputData.ParameterInput]:
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    specs = super().get_input_specs()
    specs.addParam(
      "consumes",
      param_type=InputTypes.StringListType,  # type: ignore
      required=False,
      descr=r"""The producer can either produce or consume a resource.
                  If the producer is a consumer it must be accompanied with a transfer
                  function to convert one source of energy to another.""",
    )

    specs.addParam(
      "ramp_limit",
      param_type=InputTypes.FloatType,  # type: ignore
      required=False,
      default=0,  # type: ignore
      descr=r"""Limits the rate at which production can change between consecutive
                time steps, in either a positive or negative direction, as a
                percentage of this component's capacity. For example, a generator
                with a ramp limit of 0.10 cannot increase or decrease their
                generation rate by more than 10 percent of capacity in a single
                time interval. \default{1.0}""",
    )

    specs.addParam(
      "ramp_freq",
      param_type=InputTypes.IntegerType,  # type: ignore
      required=False,
      default=0,  # type: ignore
      descr=r"""Places a limit on the number of time steps between successive
                production level ramping events. For example, if time steps are
                an hour long and the ramp frequency is set to 4, then once this
                component has changed production levels, 4 hours must pass before
                another production change can occur. Note this limit introduces
                binary variables and may require selection of appropriate solvers.
                \default{0}""",
    )

    specs.addSub(
      tf_factory.make_input_specs(
        "transfer",
        descr=r"""describes the balance between consumed and produced resources
                  for this component.""",
      )
    )

    return specs

  def __init__(self, **kwargs) -> None:
    """
    Constructor
    @ In, None
    @ Out, None
    """
    Interaction.__init__(self, **kwargs)
    self.ramp_limit = 1.0  # limiting change of production in a time step
    self.ramp_freq = 0  # time steps required between production ramping events
    self.tracking_vars = ["production"]

  def read_input(self, specs: InputData.ParameterInput, comp_name: str) -> None:
    """
    Sets settings from input file
    @ In, specs, InputData.ParameterInput, input file specification
    @ In, comp_name, str, name of component this Interaction belongs to
    @ Out, None
    """
    Interaction.read_input(self, specs, comp_name)
    self.outputs = set(specs.parameterValues["resource"])
    self.inputs = set(specs.parameterValues.get("consumes", set()))
    self.ramp_limit = specs.parameterValues.get("ramp_limit", 1.0)
    self.ramp_freq = specs.parameterValues.get("ramp_freq", 0)

    for item in specs.subparts:
      match item.getName():
        case "transfer":
          self._set_transfer_func(comp_name, item)

    if self._transfer is None and self.inputs:
      raise ProducerError(
        "Any component that consumes a resource must have a transfer function describing the production process!"
      )

    ## transfer elements are all in IO list
    if self._transfer is not None:
      self._transfer.check_io(self.inputs, self.outputs, comp_name)
      self._transfer.set_io_signs(self.inputs, self.outputs)

    ## ramp limit is (0, 1]
    if self.ramp_limit is not None and not 0 < self.ramp_limit <= 1:
      raise ProducerError(f"Ramp limit must be (0, 1] but got '{self.ramp_limit}'!")

  def _set_transfer_func(self, comp_name: str, spec: InputData.ParameterInput) -> None:
    """
    Sets up a Transfer Function
    @ In, comp_name, str, name of associated component
    @ In, spec, InputData.InputParameter, input specifications
    @ Out, None
    """
    known = tf_factory.knownTypes()
    transfer_function = None
    for sub in spec.subparts:
      if sub.getName() in known:
        if transfer_function is not None:
          raise ProducerError(f"Received multiple transfer functions for component '{comp_name}'!")
        transfer_function = tf_factory.returnInstance(sub.getName())
        transfer_function.read(comp_name, spec)
    self._transfer = transfer_function

  def get_transfer(self) -> None | TransferFunc:
    """
    Returns the transfer function, if any
    @ In, None
    @ Out, transfer, transfer ValuedParam
    """
    return self._transfer

  def print_me(self, tabs: int = 0, tab: str = "  ") -> None:
    """
    Prints info about self
    @ In, tabs, int, optional, number of tabs to insert before prints
    @ In, tab, str, optional, characters to use to denote hierarchy
    @ Out, None
    """
    pre = tab * tabs
    print(pre + "Producer:")
    print(pre + "  produces:", self.outputs)
    print(pre + "  consumes:", self.inputs)
    print(pre + "  transfer:", self._transfer)
    print(pre + "  capacity:", self._capacity)
