# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
import pytest
from pyomo.environ import Constraint
from dove.core.transfers import RatioTransfer, PolynomialTransfer

class DummyResource:
  def __init__(self, name):
    self.name = name

def test_ratio_transfer_enforces_ratio_true():
  res_in = DummyResource("in_res")
  res_out = DummyResource("out_res")
  rt = RatioTransfer(input_res=res_in, output_res=res_out, ratio=2.5)
  inputs = {"in_res": 4.0}
  outputs = {"out_res": 10.0}
  # 10.0 == 2.5 * 4.0
  assert rt(inputs, outputs) is True

def test_ratio_transfer_enforces_ratio_false():
  res_in = DummyResource("in_res")
  res_out = DummyResource("out_res")
  rt = RatioTransfer(input_res=res_in, output_res=res_out, ratio=3.0)
  inputs = {"in_res": 2.0}
  outputs = {"out_res": 5.9}
  # 5.9 != 3.0 * 2.0
  assert rt(inputs, outputs) is False

def test_ratio_transfer_only_output_skips_constraint():
  res_in = DummyResource("in_res")
  res_out = DummyResource("out_res")
  rt = RatioTransfer(input_res=res_in, output_res=res_out, ratio=1.0)
  inputs = {}
  outputs = {"out_res": 7.0}
  result = rt(inputs, outputs)
  assert result is Constraint.Skip

def test_ratio_transfer_only_input_skips_constraint():
  res_in = DummyResource("in_res")
  res_out = DummyResource("out_res")
  rt = RatioTransfer(input_res=res_in, output_res=res_out, ratio=1.0)
  inputs = {"in_res": 7.0}
  outputs = {}
  result = rt(inputs, outputs)
  assert result is Constraint.Skip

def test_ratio_transfer_no_vars_raises_value_error():
  res_in = DummyResource("in_res")
  res_out = DummyResource("out_res")
  rt = RatioTransfer(input_res=res_in, output_res=res_out, ratio=1.0)
  with pytest.raises(ValueError):
    rt({}, {})

def test_polynomial_transfer_single_term():
  # f(x) = 2 * x^2
  x = DummyResource("x")
  pt = PolynomialTransfer(terms=[(2.0, {x: 2})])
  inputs = {"x": 3.0}
  outputs = {"y": 18.0}  # total_output = 18.0
  assert pt(inputs, outputs) is True

def test_polynomial_transfer_multiple_terms():
  # f(x, z) = 1* x^1 * z^1 + 3* x^2
  x = DummyResource("x")
  z = DummyResource("z")
  terms = [
    (1.0, {x: 1, z: 1}),  # x*z
    (3.0, {x: 2})         # 3*x^2
  ]
  pt = PolynomialTransfer(terms=terms)
  inputs = {"x": 2.0, "z": 5.0}
  # expected = 1*(2*5) + 3*(2**2) = 10 + 12 = 22
  outputs = {"out1": 10.0, "out2": 12.0}
  assert pt(inputs, outputs) is True

def test_polynomial_transfer_empty_terms_zero_output():
  # no terms => expr = 0 => total_output must be 0
  pt = PolynomialTransfer(terms=[])
  inputs = {"a": 100.0}
  outputs = {"o1": 0.0, "o2": 0.0}
  assert pt(inputs, outputs) is True

def test_polynomial_transfer_mismatch_raises_false():
  # single term but outputs sum doesn't match
  x = DummyResource("x")
  pt = PolynomialTransfer(terms=[(5.0, {x: 1})])
  inputs = {"x": 2.0}
  outputs = {"y": 8.0}  # expected 5*2 = 10
  assert pt(inputs, outputs) is False
