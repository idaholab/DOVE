# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import numpy as np
import pytest

from dove.core import (
    CashFlow,
    Component,
    Converter,
    RatioTransfer,
    Resource,
    Sink,
    Source,
    Storage,
)


@pytest.mark.unit()
def test_component_basic_properties():
    comp = Component(
        name="comp", max_capacity_profile=[5.0, 4.0, 5.0], min_capacity_profile=[1.0, 1.0, 2.0]
    )
    # capacities and profile
    assert isinstance(comp.max_capacity_profile, np.ndarray)
    assert comp.max_capacity_profile.tolist() == [5.0, 4.0, 5.0]
    assert isinstance(comp.min_capacity_profile, np.ndarray)
    assert comp.min_capacity_profile.tolist() == [1.0, 1.0, 2.0]
    # empty consumes/produces
    assert comp.consumes_by_name == []
    assert comp.produces_by_name == []


@pytest.mark.unit()
@pytest.mark.parametrize(
    "kwargs, exc_type, msg_substr",
    [
        ({"produces": ["res"]}, TypeError, "all resources must be Resource"),
        ({"consumes": ["res"]}, TypeError, "all resources must be Resource"),
        ({"max_capacity_profile": [-1.0]}, ValueError, "max_capacity_profile contains negative"),
        (
            {"max_capacity_profile": [1.0], "min_capacity_profile": [2.0]},
            ValueError,
            "each value in min_capacity_profile must be in",
        ),
        ({"flexibility": "invalid"}, ValueError, "flexibility must be"),
        (
            {"max_capacity_profile": [1.0], "min_capacity_profile": [1.0, 0.5]},
            ValueError,
            "length of min_capacity_profile does not equal length of max_capacity_profile",
        ),
        ({"cashflows": [object()]}, TypeError, "all cashflows must be CashFlow"),
    ],
)
def test_component_invalid_initialization(kwargs, exc_type, msg_substr):
    init_kwargs = {"name": "bad", "max_capacity_profile": [1.0]}
    init_kwargs.update(kwargs)
    with pytest.raises(exc_type) as exc:
        Component(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_component_capacity_resource_not_in_consumes_or_produces():
    r = Resource(name="res")
    with pytest.raises(ValueError) as exc:
        Component(name="bad", max_capacity_profile=[1.0], capacity_resource=r)
    assert "capacity_resource" in str(exc.value)


@pytest.mark.unit()
def test_min_capacity_profile_set_for_fixed_flexibility():
    c = Component(name="c", max_capacity_profile=[2.0, 3.0], flexibility="fixed")
    assert c.min_capacity_profile.tolist() == [2.0, 3.0]


@pytest.mark.unit()
def test_min_capacity_profile_and_fixed_flexibility_specified_warns():
    with pytest.warns(UserWarning):
        c = Component(
            name="c",
            max_capacity_profile=[2.0, 3.0],
            min_capacity_profile=[1.0, 1.0],
            flexibility="fixed",
        )
    assert c.min_capacity_profile.tolist() == [2.0, 3.0]


@pytest.mark.unit()
def test_cf_price_profile_length_does_not_match():
    with pytest.raises(ValueError) as exc:
        Component(
            name="c",
            max_capacity_profile=[1.0],
            cashflows=[CashFlow(name="cf", price_profile=[1.0, 1.2])],
        )
    assert "cashflow price_profile length does not match" in str(exc.value)


@pytest.mark.unit()
def test_cf_price_profile_expanded():
    c = Component(
        name="c", max_capacity_profile=[1.0, 2.0], cashflows=[CashFlow(name="cf", alpha=2.0)]
    )
    assert c.cashflows[0].price_profile.tolist() == [2.0, 2.0]


@pytest.mark.unit()
def test_source_defaults_transfer_function():
    r = Resource(name="water")
    src = Source(name="src", max_capacity_profile=[10.0], produces=r)
    assert src.produces == [r]
    assert src.consumes == []
    assert src.capacity_resource is r
    tf = src.transfer_fn
    assert isinstance(tf, RatioTransfer)
    assert tf.input_resources == {} and tf.output_resources == {r: 1.0}


@pytest.mark.unit()
@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        ({"consumes": Resource(name="res")}, "consumes"),
        ({"capacity_resource": Resource(name="res")}, "capacity_resource"),
    ],
)
def test_source_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="src_bad")
    init_kwargs = {"name": "src_bad", "produces": r, "max_capacity_profile": [5.0]}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Source(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_source_with_explicit_capacity_resource():
    r = Resource(name="r")
    src = Source(name="src", produces=r, max_capacity_profile=[1.0], capacity_resource=r)
    assert src.capacity_resource is r


@pytest.mark.unit()
def test_sink_defaults_transfer_function():
    r = Resource(name="fuel")
    sink = Sink(name="sink", max_capacity_profile=[8.0], consumes=r)
    assert sink.consumes == [r]
    assert sink.produces == []
    assert sink.capacity_resource is r
    tf = sink.transfer_fn
    assert isinstance(tf, RatioTransfer)
    assert tf.input_resources == {r: 1.0} and tf.output_resources == {}


@pytest.mark.unit()
@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        ({"produces": Resource(name="res")}, "produces"),
        ({"capacity_resource": Resource(name="res")}, "capacity_resource"),
    ],
)
def test_sink_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="sink_bad")
    init_kwargs = {"name": "sink_bad", "consumes": r, "max_capacity_profile": [5.0]}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Sink(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_sink_with_explicit_capacity_resource():
    r = Resource(name="r")
    sink = Sink(name="sink", consumes=r, max_capacity_profile=[1.0], capacity_resource=r)
    assert sink.capacity_resource is r


@pytest.mark.unit()
def test_converter_same_resource_sets_capacity_and_warns():
    r = Resource(name="electricity")
    with pytest.warns(UserWarning):
        conv = Converter(
            name="conv",
            max_capacity_profile=[15.0],
            consumes=[r],
            produces=[r],
            transfer_fn=RatioTransfer(input_resources={r: 1.0}, output_resources={r: 1.0}),
        )
    assert conv.capacity_resource is r


@pytest.mark.unit()
@pytest.mark.parametrize("has_transfer_fn", [True, False])
def test_converter_ambiguous_capacity_resource_requires_explicit(has_transfer_fn):
    r1 = Resource(name="in_res")
    r2 = Resource(name="out_res")
    init_kwargs = {"name": "amb", "max_capacity_profile": [5.0], "consumes": [r1], "produces": [r2]}
    if has_transfer_fn:
        init_kwargs.update(
            {"transfer_fn": RatioTransfer(input_resources={r1: 1.0}, output_resources={r2: 1.0})}
        )
    # missing transfer_fn and ambiguous resources
    with pytest.raises(ValueError) as exc:
        Converter(**init_kwargs)
    assert "ambiguous capacity_resource" in str(exc.value)


@pytest.mark.unit()
def test_storage_default_capacity_and_valid_ranges():
    r = Resource(name="stor_res")
    st = Storage(name="stor", max_capacity_profile=[20.0], resource=r)
    assert st.resource is r
    assert st.capacity_resource is r
    # default attributes are in [0,1]
    for attr in ("rte", "max_charge_rate", "max_discharge_rate", "initial_stored"):
        val = getattr(st, attr)
        assert 0.0 <= val <= 1.0


@pytest.mark.unit()
@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        ({"produces": Resource(name="res")}, "produces"),
        ({"consumes": Resource(name="res")}, "consumes"),
        ({"capacity_resource": Resource(name="res")}, "capacity_resource"),
        ({"rte": 1.5}, "rte"),
        ({"max_charge_rate": -0.1}, "max_charge_rate"),
        ({"max_discharge_rate": 2.0}, "max_discharge_rate"),
        ({"initial_stored": -0.5}, "initial_stored"),
    ],
)
def test_storage_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="stor_bad")
    init_kwargs = {"name": "stor_bad", "max_capacity_profile": [5.0], "resource": r}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Storage(**init_kwargs)
    assert msg_substr in str(exc.value)
