# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
# from ravenframework.EntityFactoryBase import EntityFactory
""" """

import warnings

from ravenframework.utils.InputData import InputTypes, Quantity

from dove.physics import Polynomial, Ratio

from .autospec import AutoSpec
from .simple_spec import SimpleNodeSpec


class RateSpec(SimpleNodeSpec):
  """ """

  node_name = "rate"
  content_type = InputTypes.FloatType
  description = r"""linear coefficient for the indicated \xmlAttr{resource}."""
  params = {
    "resource": (
      InputTypes.StringType,
      False,
      None,
      r"""
      indicates the resource for which the linear transfer ratio is being
      provided in this node.
      """,
    )
  }


class CoeffSpec(SimpleNodeSpec):
  """ """

  node_name = "coeff"
  content_type = InputTypes.FloatType
  description = r"""
  one coefficient for one poloynomial term of the specified \xmlAttr{resources}.
  Care should be taken to assure the sign of the coefficient is working as expected,
  as consumed resources have a negative sign while produced resources have a positive
  sign, and the full equation should have the form 0 = ... .
  """
  params = {
    "resource": (
      InputTypes.StringListType,
      False,
      None,
      r"""
      indicates the resource(s) for which the polynomial coefficient is being provided in this node.
      Note that the order of the resources matters for specifying the polynomial \xmlAttr{order}.
      """,
    ),
    "order": (
      InputTypes.IntegerListType,
      False,
      None,
      r"""
      indicates the orders of the polynomial for each resource specified, in order.
      For example, if \xmlAttr{resources} is ``x, y'', then order ``2,3'' would mean
      the specified coefficient is for $x^{2}y^{3}$.
      """,
    ),
  }


class TransferSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls):
    """ """
    cls.createClass(
      "transfer",
      ordered=True,
      descr=r"""
      describes the balance between consumed and produced resources
      for this component.
      """,
    )
    cls.addSub(RatioSpec.getInputSpecification(), quantity=Quantity.zero_to_one)
    cls.addSub(PolySpec.getInputSpecification(), quantity=Quantity.zero_to_one)
    return cls

  def instantiate(self):
    return self.subparts[0].instantiate()


class RatioSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls):
    """ """
    cls.createClass(
      "ratio",
      contentType=InputTypes.StringType,
      descr=r"""
      indicates this transfer function is a constant linear combination of resources.
      For example, a balance equation might be written as 3a + 7b -> 2c, implying
      that to make 2c, it always takes 3 parts a and 7 parts b, or the balance ratio
      (3a, 7b, 2c). This means that the ratio of (3, 7, 2) must be maintained between
      (a, b, c) for all production levels. Note that the coefficient signs are
      automatically fixed internally to be negative for consumed quantities and
      positive for produced resources, regardless of signs used by the user.
      For an equation-based transfer function instead of balance ratio, see Polynomial.
      """,
    )
    cls.addSub(RateSpec.getInputSpecification())
    cls.associated_class = Ratio
    return cls

  def instantiate(self):
    """ """
    coefficient = {}
    for rate_node in self.findAll("rate"):
      rate = rate_node.instantiate()
      resource = rate["resource"]
      coefficient[resource] = rate["value"]
    return self.associated_class(coefficient)


class PolySpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls):
    """ """
    cls.createClass(
      "poly",
      contentType=InputTypes.StringType,
      descr=r"""
      indicates this transfer function is expressed by a polynomial relationship of arbitrary order.
      Note the polynomial must be specified in weak form, with all terms on one side of the equation
      set equal to zero. For instance, the equation $ax^2 + bx + c = dy^2 + fy + g$ should be reformulated
      as $ax^2 + bx + (c-g) - dy^2 - fy = 0$.
      """,
    )

    cls.addSub(CoeffSpec.getInputSpecification())

    return cls
