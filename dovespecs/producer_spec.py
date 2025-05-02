# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import Any
from ravenframework.utils.InputData import InputTypes

from .autospec import AutoSpec
from .interaction_spec import InteractionSpec
from .transfer_spec import TransferSpec


class ProducerSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("produces", baseNode=InteractionSpec.getInputSpecification())
    cls.addParam(
      "consumes",
      param_type=InputTypes.StringListType,  # type: ignore
      required=False,
      descr=r"""
      The producer can either produce or consume a resource. If the producer is
      a consumer it must be accompanied with a transfer function to convert one
      source of energy to another.
      """,
    )

    cls.addParam(
      "ramp_limit",
      param_type=InputTypes.FloatType,  # type: ignore
      required=False,
      default=0,  # type: ignore
      descr=r"""
      Limits the rate at which production can change between consecutive time
      steps, in either a positive or negative direction, as a percentage of this
      component's capacity. For example, a generator with a ramp limit of 0.10
      cannot increase or decrease their generation rate by more than 10 percent
      of capacity in a single time interval. \default{1.0}
      """,
    )

    cls.addParam(
      "ramp_freq",
      param_type=InputTypes.IntegerType,  # type: ignore
      required=False,
      default="0",
      descr=r"""
      Places a limit on the number of time steps between successive production
      level ramping events. For example, if time steps are an hour long and the
      ramp frequency is set to 4, then once this component has changed production
      levels, 4 hours must pass before another production change can occur.
      Note this limit introduces binary variables and may require selection of
      appropriate solvers. \default{0}
      """,
    )

    cls.addSub(TransferSpec.getInputSpecification())
    return cls

  def instantiate(self) -> dict[str, Any]:
    """ """
    producer_args = {}
    producer_args["produces"] = self.parameterValues.get("resource")
    producer_args["consumes"] = self.parameterValues.get("consumes", [])
    producer_args["ramp_limit"] = self.parameterValues.get("ramp_limit")
    producer_args["ramp_freq"] = self.parameterValues.get("ramp_freq")
    transfer = self.findFirst("transfer")
    if transfer is not None:
      producer_args["transfer"] = transfer.instantiate()

    return producer_args
