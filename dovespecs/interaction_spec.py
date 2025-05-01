# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Interaction Input Specification
"""

from ravenframework.utils.InputData import InputTypes

from dove.interactions import Producer, Storage, Demand

from .autospec import AutoSpec
from .special import CapacitySpec, CapacityFactorSpec, MinimumSpec, InitialStoredSpec, StrategySpec
from .transfer_spec import TransferSpec


class InteractionSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("interaction")
    cls.addParam(
      "resource",
      param_type=InputTypes.StringListType,  # type: ignore
      required=True,
    )

    cls.addParam(
      "dispatch",
      param_type=InputTypes.makeEnumType("dispatch_opts", "dispatch_opts", ["fixed", "independent", "dependent"]),  # type: ignore
      required=True,
      descr=r"""
      describes the way this component should be dispatched, or its flexibility.
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
      usage from the changing behavior of other components.
      """,
    )

    cls.addSub(CapacitySpec.getInputSpecification())
    cls.addSub(CapacityFactorSpec.getInputSpecification())
    cls.addSub(MinimumSpec.getInputSpecification())
    return cls

  def instantiate(self):
    """"""
    return None


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
    cls.associated_class = Producer
    return cls

  def instantiate(self) -> Producer:
    """ """
    cap = self.findFirst("capacity").instantiate()
    cap_var = cap["resource"]
    capacity = cap["value"]
    return Producer()


class StorageSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("stores", baseNode=InteractionSpec.getInputSpecification())
    cls.addParam(
      "periodic_level",
      param_type=InputTypes.BoolType,  # type: ignore
      required=False,
      default="True",
      descr=r"""
      indicates whether the level of the storage should be required to
      return to its initial level within each modeling window. If True,
      this reduces the flexibility of the storage, but if False, can
      result in breaking conservation of resources. \default{True}.
      """,
    )

    cls.addParam(
      "rte",
      param_type=InputTypes.FloatType,  # type: ignore
      required=False,
      default="1.0",
      descr=r"""
      round-trip efficiency for this component as a scalar multiplier. \default{1.0}
      """,
    )

    cls.addParam(
      "max_charge_rate",
      param_type=InputTypes.FloatType,  # type: ignore
      required=False,
      default="1.0",
      descr=r"""
      maximum storage charge rate as a fraction of the storage capacity,
      from 0 to 1. \default{1.0}
      """,
    )

    cls.addParam(
      "max_discharge_rate",
      param_type=InputTypes.FloatType,  # type: ignore
      required=False,
      default="1.0",
      descr=r"""
      maximum storage discharge rate as a fraction of the storage capacity,
      from 0 to 1. \default{1.0}
      """,
    )

    cls.addSub(InitialStoredSpec.getInputSpecification())
    cls.addSub(StrategySpec.getInputSpecification())
    # TODO: Need to revisit strategy param for DOVE since no functions
    return cls

  def instantiate(self) -> Storage:
      """ """
      return Storage()

class DemandSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("demands", baseNode=InteractionSpec.getInputSpecification())

    return cls

  def instantiate(self) -> Demand:
    """ """
    return Demand()
