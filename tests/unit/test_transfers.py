# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import pytest

from dove.core import Resource
from dove.core.transfers import PolynomialTransfer, RatioTransfer


@pytest.mark.unit()
def test_siso_ratio_transfer_enforces_ratio_true():
    res_in = Resource("in_res")
    res_out = Resource("out_res")
    rt = RatioTransfer(input_resources={res_in: 1.0}, output_resources={res_out: 2.5})
    inputs = {"in_res": 4.0}
    outputs = {"out_res": 10.0}
    # 10.0 == 2.5 * 4.0
    result_reqs = rt(inputs, outputs)
    assert len(result_reqs) == 1
    assert result_reqs[0] is True


@pytest.mark.unit()
def test_siso_ratio_transfer_enforces_ratio_false():
    res_in = Resource("in_res")
    res_out = Resource("out_res")
    rt = RatioTransfer(input_resources={res_in: 1.0}, output_resources={res_out: 3.0})
    inputs = {"in_res": 2.0}
    outputs = {"out_res": 5.9}
    # 5.9 != 3.0 * 2.0
    result_reqs = rt(inputs, outputs)
    assert len(result_reqs) == 1
    assert result_reqs[0] is False


@pytest.mark.unit()
def test_mimo_ratio_transfer_enforces_ratio_true():
    res_in_1 = Resource("in_res_1")
    res_in_2 = Resource("in_res_2")
    res_out_1 = Resource("out_res_1")
    res_out_2 = Resource("out_res_2")
    rt = RatioTransfer(
        input_resources={res_in_1: 1.0, res_in_2: 2.0},
        output_resources={res_out_1: 1.5, res_out_2: 2.5},
    )
    inputs = {"in_res_1": 3.0, "in_res_2": 6.0}
    outputs = {"out_res_1": 4.5, "out_res_2": 7.5}
    # 3.0/1.0 == 6.0/2.0 == 4.5/1.5 == 7.5/2.5
    result_reqs = rt(inputs, outputs)
    assert len(result_reqs) == 3
    assert all(req is True for req in result_reqs)


@pytest.mark.unit()
def test_mimo_ratio_transfer_enforces_ratio_wrong_input():
    res_in_1 = Resource("in_res_1")
    res_in_2 = Resource("in_res_2")
    res_out_1 = Resource("out_res_1")
    res_out_2 = Resource("out_res_2")
    rt = RatioTransfer(
        input_resources={res_in_1: 1.0, res_in_2: 2.0},
        output_resources={res_out_1: 1.5, res_out_2: 2.5},
    )
    inputs = {"in_res_1": 6.0, "in_res_2": 6.0}  # in_res_1 should be 3, not 6
    outputs = {"out_res_1": 4.5, "out_res_2": 7.5}
    # 6.0/1.0 != 6.0/2.0 == 4.5/1.5 == 7.5/2.5
    result_reqs = rt(inputs, outputs)
    assert len(result_reqs) == 3
    assert not all(req is True for req in result_reqs)


@pytest.mark.unit()
def test_mimo_ratio_transfer_enforces_ratio_wrong_output():
    res_in_1 = Resource("in_res_1")
    res_in_2 = Resource("in_res_2")
    res_out_1 = Resource("out_res_1")
    res_out_2 = Resource("out_res_2")
    rt = RatioTransfer(
        input_resources={res_in_1: 1.0, res_in_2: 2.0},
        output_resources={res_out_1: 1.5, res_out_2: 2.5},
    )
    inputs = {"in_res_1": 3.0, "in_res_2": 6.0}
    outputs = {"out_res_1": 4.5, "out_res_2": 6.0}  # out_res_2 should be 7.5, not 6
    # 3.0/1.0 == 6.0/2.0 == 4.5/1.5 != 6.0/2.5
    result_reqs = rt(inputs, outputs)
    assert len(result_reqs) == 3
    assert not all(req is True for req in result_reqs)


@pytest.mark.unit()
def test_ratio_transfer_only_output_raises_value_error():
    res_in = Resource("in_res")
    res_out = Resource("out_res")
    rt = RatioTransfer(input_resources={res_in: 1.0}, output_resources={res_out: 1.0})
    inputs = {}
    outputs = {"out_res": 7.0}
    with pytest.raises(ValueError):
        rt(inputs, outputs)


@pytest.mark.unit()
def test_ratio_transfer_only_input_raises_value_error():
    res_in = Resource("in_res")
    res_out = Resource("out_res")
    rt = RatioTransfer(input_resources={res_in: 1.0}, output_resources={res_out: 1.0})
    inputs = {"in_res": 7.0}
    outputs = {}
    with pytest.raises(ValueError):
        rt(inputs, outputs)


@pytest.mark.unit()
def test_ratio_transfer_no_vars_raises_value_error():
    res_in = Resource("in_res")
    res_out = Resource("out_res")
    rt = RatioTransfer(input_resources={res_in: 1.0}, output_resources={res_out: 1.0})
    with pytest.raises(ValueError):
        rt({}, {})


@pytest.mark.unit()
def test_polynomial_transfer_single_term():
    # f(x) = 2 * x^2
    x = Resource("x")
    pt = PolynomialTransfer(terms=[(2.0, {x: 2})])
    inputs = {"x": 3.0}
    outputs = {"y": 18.0}  # total_output = 18.0
    result_reqs = pt(inputs, outputs)
    assert len(result_reqs) == 1
    assert result_reqs[0] is True


@pytest.mark.unit()
def test_polynomial_transfer_multiple_terms():
    # f(x, z) = 1* x^1 * z^1 + 3* x^2
    x = Resource("x")
    z = Resource("z")
    terms = [
        (1.0, {x: 1, z: 1}),  # x*z
        (3.0, {x: 2}),  # 3*x^2
    ]
    pt = PolynomialTransfer(terms=terms)
    inputs = {"x": 2.0, "z": 5.0}
    # expected = 1*(2*5) + 3*(2**2) = 10 + 12 = 22
    outputs = {"out1": 10.0, "out2": 12.0}
    result_reqs = pt(inputs, outputs)
    assert len(result_reqs) == 1
    assert result_reqs[0] is True


@pytest.mark.unit()
def test_polynomial_transfer_empty_terms_zero_output():
    # no terms => expr = 0 => total_output must be 0
    pt = PolynomialTransfer(terms=[])
    inputs = {"a": 100.0}
    outputs = {"o1": 0.0, "o2": 0.0}
    result_reqs = pt(inputs, outputs)
    assert len(result_reqs) == 1
    assert result_reqs[0] is True


@pytest.mark.unit()
def test_polynomial_transfer_mismatch_raises_false():
    # single term but outputs sum doesn't match
    x = Resource("x")
    pt = PolynomialTransfer(terms=[(5.0, {x: 1})])
    inputs = {"x": 2.0}
    outputs = {"y": 8.0}  # expected 5*2 = 10
    result_reqs = pt(inputs, outputs)
    assert len(result_reqs) == 1
    assert result_reqs[0] is False
