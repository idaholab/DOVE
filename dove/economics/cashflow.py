# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
CashFlow Module
"""
from typing import Any
from collections import defaultdict

from ravenframework.utils import InputData, InputTypes

class CashFlow:
  """
  Hold the economics for a single cash flow, C = m * a * (D/D')^x
  where:
    C is the cashflow ($)
    m is a scalar multiplier
    a is the value of the widget, based on the D' volume sold
    D is the amount of widgets sold
    D' is the nominal amount of widgets sold
    x is the scaling factor
  """
  def __repr__(self) -> str:
    """
    String representation.
    @ In, None
    @ Out, __repr__, string representation
    """
    return f'<DOVE CashFlow "{self.name}">'

  def __init__(self, component) -> None:
    """
    Constructor
    @ In, component, CashFlowUser instance, cash flow user to which this cash flow belongs
    @ Out, None
    """

    self._driver = None  # ValuedParam "quantity produced", D
    self._alpha = None  # ValuedParam "price per produced", a
    self._reference_driver = None  # ValuedParam "where price is accurate", D'
    self._scaling_factor_x = None  # ValuedParam "economy of scale", x

    self.component = component  # component instance to whom this cashflow belongs, if any
    self.name: str = "placeholder"  # base name of cash flow
    self.has_inflation: bool = False  # apply inflation or not
    self.is_npv_exempt: bool = False  # exclude cashflow in NPV calculation?
    self.is_price_levelized: bool = False
    self.is_taxable: bool = True
    self.depreciation: None | int = None

    self.type: str = "repeating"  # needed? one-time, yearly, repeating
    self.period: str = "hour"  # period for recurring cash flows
    self._signals = set()  # variable values needed for this cash flow
    self._crossrefs: defaultdict[str, Any] = defaultdict(dict)


  def _set_value(self, name, spec) -> None:
    """
    """
    setattr(self, name, spec.value)

  def _set_fixed_param(self, name, value) -> None:
    """
    """
    setattr(self, name, value)

  def read_input(self, item) -> None:
    """
    Sets settings from input file
    @ In, item, InputData.ParameterInput, parsed specs from user
    @ Out, None
    """
    self.name = item.parameterValues["name"] # required or fails
    self.type = item.parameterValues["type"] # required or fails
    self.period = item.parameterValues.get("period", self.period)
    self.is_taxable = item.parameterValues.get("taxable", self.is_taxable)
    self.is_npv_exempt = item.parameterValues.get("npv_exempt", self.is_npv_exempt)
    self.has_inflation = item.parameterValues.get("inflation", self.has_inflation)
    self.depreciation = item.parameterValues.get("depreciate", self.depreciation)

    for sub in item.subparts:
      match (item_name := sub.getName()):
        case "driver" | "reference_driver" | "scaling_factor_x":
          self._set_value(f"_{item_name}", sub)
        case "reference_price":
          self.set_reference_price(sub)
        case _:
          raise IOError(f"Unrecognized 'CashFlow' node: {item_name}")

    if self._driver is None:
      raise IOError(f"No <driver> node provided for CashFlow {self.name}!")
    if self._reference_driver is None:
      self._set_fixed_param("_reference_driver", 1)
    if self._scaling_factor_x is None:
      self._set_fixed_param("_scaling_factor_x", 1)

  def set_reference_price(self, node) -> None:
    """
    Sets the reference_price attribute based on given ValuedParam or if Levelized Cost
    @ In, node, InputParams.ParameterInput, reference_price head node
    @ Out, price_is_levelized, bool, are we computing levelized cost for this cashflow?
    """
    for sub in node.subparts:
      if sub.name == "levelized_cost":
        self.is_price_levelized = True
        __ = node.popSub("levelized_cost")

    try:
      self._set_value("_alpha", node)
    except AttributeError as e:
      if self.is_price_levelized:
        self._set_fixed_param("_alpha", 1)
      else:
        raise IOError(f"No <reference_price> node provided for CashFlow {self.name}!")

  def evaluate_cost(self, activity, meta):
    pass

  def calculate_params(self, meta):
    pass

  def get_driver(self):
    """
    Getter for Cashflow Driver
    @ In, None
    @ Out, driver, ValuedParam, valued param for the cash flow driver
    """
    return self._driver
