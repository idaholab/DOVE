# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from ravenframework.utils.InputData import InputTypes

from .interaction_spec import InteractionSpec
from .autospec import AutoSpec
from .special import InitialStoredSpec, StrategySpec


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

  def instantiate(self):
    """ """
    storage_args = {}
    storage_args["consumes"] = self.parameterValues.get("resource")
    storage_args["produces"] = self.parameterValues.get("resource")
    storage_args["periodic_level"] = self.parameterValues.get("periodic_level")
    storage_args["rte"] = self.parameterValues.get("rte")
    storage_args["max_charge_rate"] = self.parameterValues.get("max_charge_rate")
    storage_args["max_discharge_rate"] = self.parameterValues.get("max_discharge_rate")

    init_stored = self.findFirst("initial_stored")
    strategy = self.findFirst("strategy")

    if init_stored is not None:
      storage_args["initial_stored"] = init_stored["value"]

    if strategy is not None:
      storage_args["strategy"] = strategy["value"]

    return storage_args
