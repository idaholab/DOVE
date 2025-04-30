# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Interaction Input Specification
"""

from ravenframework.utils.InputData import InputTypes, parameterInputFactory, Quantity

from .autospec import AutoSpec


class InteractionSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("interaction", ordered=True)
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

    cap = parameterInputFactory(
      "capacity",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""
      the maximum value at which this component can act, in units corresponding
      to the indicated resource.
      """,
    )

    cap.addParam(
      "resource",
      param_type=InputTypes.StringType,
      descr=r"""
      indicates the resource that defines the capacity of this component's
      operation. For example, if a component consumes steam and electricity
      to produce hydrogen, the capacity of the component can be defined by
      the maximum steam consumable, maximum electricity consumable, or maximum
      hydrogen producable. Any choice should be nominally equivalent, but
      determines the units of the value of this node.
      """,
    )
    cls.addSub(cap, quantity=Quantity.zero_to_one)

    capfactor = parameterInputFactory(
      "capacity_factor",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""
      the actual value at which this component can act, as a unitless
      fraction of total rated capacity. Note that these factors are applied
      within the dispatch optimization; we assume that the capacity factor
      is not a variable in the outer optimization.
      """,
    )
    cls.addSub(capfactor)

    minn = parameterInputFactory(
      "minimum",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""
      provides the minimum value at which this component can act, in units of
      the indicated resource.
      """,
    )

    minn.addParam(
      "resource",
      param_type=InputTypes.StringType,
      descr=r"""
      indicates the resource that defines the minimum activity level for this
      component, as with the component's capacity.
      """,
    )
    cls.addSub(minn)
    return cls


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

    # cls.addSub(
    #   tf_factory.make_input_specs(
    #     "transfer",
    #     descr=r"""describes the balance between consumed and produced resources
    #               for this component.""",
    #   )
    # )
    return cls


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

    cls.addSub(
      parameterInputFactory(
        "initial_stored",
        contentType=InputTypes.FloatOrIntType,
        descr=r"""
        indicates what percent of the storage unit is full at the start
        of each optimization sequence, from 0 to 1. \default{0.0}.
        """,
      ),
    )

    # TODO: Need to revisit strategy param for DOVE since no functions are expected.
    cls.addSub(
      parameterInputFactory(
        "strategy",
        contentType=InputTypes.StringType,
        descr=r"""
        control strategy for operating the storage. If not specified,
        uses a perfect foresight strategy.
        """,
      ),
    )

    return cls


class DemandSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
    cls.createClass("demands", baseNode=InteractionSpec.getInputSpecification())

    return cls
