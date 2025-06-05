# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import numpy as np
import pytest

from dove.core import (
    Component,
    Converter,
    RatioTransfer,
    Resource,
    Sink,
    Source,
    Storage,
)


def test_component_basic_properties_and_profile_conversion():
    comp = Component(name="comp", max_capacity=5.0, min_capacity=1.0, profile=[0.1, 0.2, 0.3])
    # capacities and profile
    assert comp.max_capacity == 5.0
    assert comp.min_capacity == 1.0
    assert isinstance(comp.profile, np.ndarray)
    assert comp.profile.tolist() == [0.1, 0.2, 0.3]
    # empty consumes/produces
    assert comp.consumes_by_name == []
    assert comp.produces_by_name == []


@pytest.mark.parametrize(
    "kwargs, exc_type, msg_substr",
    [
        ({"produces": "res"}, TypeError, "produces must be a list"),
        ({"consumes": "res"}, TypeError, "consumes must be a list"),
        ({"produces": ["res"]}, TypeError, "all resources must be Resource"),
        ({"consumes": ["res"]}, TypeError, "all resources must be Resource"),
        ({"max_capacity": -1.0}, ValueError, "max_capacity < 0"),
        ({"max_capacity": 1.0, "min_capacity": 2.0}, ValueError, "min_capacity (2.0) must be in"),
        ({"profile": [-0.5]}, ValueError, "profile contains negative"),
        (
            {"capacity_factor": True, "profile": [-0.1, 0.5]},
            ValueError,
            "capacity_factor profile must",
        ),
        (
            {"capacity_factor": True, "profile": [0.5, 1.2]},
            ValueError,
            "capacity_factor profile must",
        ),
        ({"flexibility": "invalid"}, ValueError, "flexibility must be"),
        ({"cashflows": [object()]}, TypeError, "all cashflows must be CashFlow"),
    ],
)
def test_component_invalid_initialization(kwargs, exc_type, msg_substr):
    init_kwargs = {"name": "bad", "max_capacity": 1.0}
    init_kwargs.update(kwargs)
    with pytest.raises(exc_type) as exc:
        Component(**init_kwargs)
    assert msg_substr in str(exc.value)


def test_component_capacity_resource_not_in_consumes_or_produces():
    r = Resource(name="res")
    with pytest.raises(ValueError) as exc:
        Component(name="bad", max_capacity=1.0, capacity_resource=r)
    assert "capacity_resource" in str(exc.value)


def test_source_defaults_transfer_function():
    r = Resource(name="water")
    src = Source(name="src", max_capacity=10.0, produces=r)
    assert src.produces == [r]
    assert src.consumes == []
    assert src.capacity_resource is r
    tf = src.transfer_fn
    assert isinstance(tf, RatioTransfer)
    assert tf.input_res is r and tf.output_res is r and tf.ratio == 1.0


@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        ({"consumes": Resource(name="res")}, "consumes"),
        ({"capacity_resource": Resource(name="res")}, "capacity_resource"),
    ],
)
def test_source_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="src_bad")
    init_kwargs = {"name": "src_bad", "produces": r, "max_capacity": 5.0}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Source(**init_kwargs)
    assert msg_substr in str(exc.value)


def test_sink_defaults_transfer_function():
    r = Resource(name="fuel")
    sink = Sink(name="sink", max_capacity=8.0, consumes=r)
    assert sink.consumes == [r]
    assert sink.produces == []
    assert sink.capacity_resource is r
    tf = sink.transfer_fn
    assert isinstance(tf, RatioTransfer)
    assert tf.input_res is r and tf.output_res is r and tf.ratio == 1.0


@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        ({"produces": Resource(name="res")}, "produces"),
        ({"capacity_resource": Resource(name="res")}, "capacity_resource"),
    ],
)
def test_sink_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="sink_bad")
    init_kwargs = {"name": "sink_bad", "consumes": r, "max_capacity": 5.0}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Sink(**init_kwargs)
    assert msg_substr in str(exc.value)


def test_converter_same_resource_sets_capacity_and_warns():
    r = Resource(name="electricity")
    with pytest.warns(UserWarning):
        conv = Converter(
            name="conv",
            max_capacity=15.0,
            consumes=[r],
            produces=[r],
            transfer_fn=RatioTransfer(input_res=r, output_res=r),
        )
    assert conv.capacity_resource is r


@pytest.mark.parametrize("has_transfer_fn", [True, False])
def test_converter_ambiguous_capacity_resource_requires_explicit(has_transfer_fn):
    r1 = Resource(name="in_res")
    r2 = Resource(name="out_res")
    init_kwargs = {"name": "amb", "max_capacity": 5.0, "consumes": [r1], "produces": [r2]}
    if has_transfer_fn:
        init_kwargs.update({"transfer_fn": RatioTransfer(input_res=r1, output_res=r2)})
    # missing transfer_fn and ambiguous resources
    with pytest.raises(ValueError) as exc:
        Converter(**init_kwargs)
    assert "ambiguous capacity_resource" in str(exc.value)


def test_converter_no_transfer_fn():
    r1 = Resource(name="r1")
    r2 = Resource(name="r2")
    with pytest.raises(ValueError) as exc:
        Converter(
            name="bad_conv", max_capacity=1, consumes=[r1], produces=[r2], capacity_resource=r1
        )
    assert "transfer_fn specified" in str(exc.value)


def test_storage_default_capacity_and_valid_ranges():
    r = Resource(name="stor_res")
    st = Storage(name="stor", max_capacity=20.0, resource=r)
    assert st.resource is r
    assert st.capacity_resource is r
    # default attributes are in [0,1]
    for attr in ("rte", "max_charge_rate", "max_discharge_rate", "initial_stored"):
        val = getattr(st, attr)
        assert 0.0 <= val <= 1.0


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
    init_kwargs = {"name": "stor_bad", "max_capacity": 5.0, "resource": r}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Storage(**init_kwargs)
    assert msg_substr in str(exc.value)
