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


@pytest.mark.unit()
def test_component_basic_properties():
    comp = Component(
        name="comp",
        installed_capacity=5.0,
        capacity_factor=[1.0, 0.8],
        min_capacity_factor=[0.2, 0.4],
    )
    # capacities and profile
    assert comp.installed_capacity == 5.0
    assert isinstance(comp.capacity_factor, np.ndarray)
    assert comp.capacity_factor.tolist() == [1.0, 0.8]
    assert isinstance(comp.min_capacity_factor, np.ndarray)
    assert comp.min_capacity_factor.tolist() == [0.2, 0.4]
    # empty consumes/produces
    assert comp.consumes_by_name == []
    assert comp.produces_by_name == []
    # test capacity/minimum getters when cap factor and min are provided
    assert comp.capacity_at_timestep(0) == 5.0
    assert comp.capacity_at_timestep(1) == 4.0
    assert comp.minimum_at_timestep(0) == 1.0
    assert comp.minimum_at_timestep(1) == 2.0


@pytest.mark.unit()
def test_component_getters_with_no_time_series():
    comp = Component(name="comp", installed_capacity=2.0)
    assert comp.capacity_at_timestep(1876) == 2.0  # should be the same for any timestep
    assert comp.minimum_at_timestep(2025) == 0.0  # minimum should always be zero


@pytest.mark.unit()
def test_component_capacity_getter_bad_timestep():
    comp = Component(
        name="comp",
        installed_capacity=5.0,
        capacity_factor=[1.0, 0.8, 1.0],
    )
    with pytest.raises(IndexError) as exc:
        comp.capacity_at_timestep(4)
    assert "outside of range for provided capacity_factor data" in str(exc.value)


@pytest.mark.unit()
def test_component_minimum_getter_bad_timestep():
    comp = Component(
        name="comp",
        installed_capacity=5.0,
        min_capacity_factor=[0.2, 0.2, 0.4],
    )
    with pytest.raises(IndexError) as exc:
        comp.minimum_at_timestep(4)
    assert "outside of range for provided min_capacity_factor data" in str(exc.value)


@pytest.mark.unit()
@pytest.mark.parametrize(
    "kwargs, exc_type, msg_substr",
    [
        ({"produces": ["res"]}, TypeError, "all resources must be Resource"),
        ({"consumes": ["res"]}, TypeError, "all resources must be Resource"),
        ({"installed_capacity": -1.0}, ValueError, "cannot be negative"),
        (
            {"installed_capacity": 10.0, "capacity_factor": [0.1], "min_capacity_factor": [0.2]},
            ValueError,
            "minimum activity value at timestep",
        ),
        ({"capacity_factor": [1.2]}, ValueError, "capacity_factor value at timestep"),
        ({"min_capacity_factor": [1.2]}, ValueError, "min_capacity_factor value at timestep"),
        ({"flexibility": "invalid"}, ValueError, "flexibility must be"),
        ({"cashflows": [object()]}, TypeError, "all cashflows must be CashFlow"),
    ],
)
def test_component_invalid_initialization(kwargs, exc_type, msg_substr):
    init_kwargs = {"name": "bad", "installed_capacity": 1.0}
    init_kwargs.update(kwargs)
    with pytest.raises(exc_type) as exc:
        Component(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_component_capacity_resource_not_in_consumes_or_produces():
    r = Resource(name="res")
    with pytest.raises(ValueError) as exc:
        Component(name="bad", installed_capacity=1.0, capacity_resource=r)
    assert "capacity_resource" in str(exc.value)


@pytest.mark.unit()
def test_min_capacity_factor_and_fixed_flexibility_specified_warns():
    with pytest.warns(UserWarning):
        Component(
            name="c",
            installed_capacity=4.0,
            capacity_factor=[0.5, 0.75],
            min_capacity_factor=[0.25, 0.25],
            flexibility="fixed",
        )


@pytest.mark.unit()
def test_source_defaults_transfer_function():
    r = Resource(name="water")
    src = Source(name="src", installed_capacity=10.0, produces=r)
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
    init_kwargs = {"name": "src_bad", "produces": r, "installed_capacity": 5.0}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Source(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_source_with_explicit_capacity_resource():
    r = Resource(name="r")
    src = Source(name="src", produces=r, installed_capacity=1.0, capacity_resource=r)
    assert src.capacity_resource is r


@pytest.mark.unit()
def test_sink_defaults_transfer_function():
    r = Resource(name="fuel")
    sink = Sink(name="sink", demand_profile=[8.0], consumes=r)
    assert sink.consumes == [r]
    assert sink.produces == []
    assert sink.capacity_resource is r
    tf = sink.transfer_fn
    assert isinstance(tf, RatioTransfer)
    assert tf.input_resources == {r: 1.0} and tf.output_resources == {}


@pytest.mark.unit()
def test_sink_capacity_getter_with_demand_profile():
    r = Resource(name="res")
    sink = Sink(name="sink", consumes=r, demand_profile=[4.0, 3.0])
    assert sink.capacity_at_timestep(0) == 4.0
    assert sink.capacity_at_timestep(1) == 3.0
    with pytest.raises(IndexError) as exc:
        sink.capacity_at_timestep(2)
    assert "outside of range for provided demand_profile data" in str(exc.value)


@pytest.mark.unit()
def test_sink_capacity_getter_with_installed_cap():
    r = Resource(name="res")
    sink = Sink(name="sink", consumes=r, installed_capacity=4.0, capacity_factor=[0, 0.5])
    assert sink.capacity_at_timestep(0) == 0.0
    assert sink.capacity_at_timestep(1) == 2.0
    with pytest.raises(IndexError) as exc:
        sink.capacity_at_timestep(2)
    assert "outside of range for provided capacity_factor data" in str(exc.value)


@pytest.mark.unit()
def test_sink_minimum_getter_with_min_demand_profile():
    r = Resource(name="res")
    sink = Sink(name="sink", consumes=r, demand_profile=[4.0], min_demand_profile=[2.0])
    assert sink.minimum_at_timestep(0) == 2.0
    with pytest.raises(IndexError) as exc:
        sink.minimum_at_timestep(1)
    assert "outside of range for provided min_demand_profile data" in str(exc.value)


@pytest.mark.unit()
def test_sink_minimum_getter_with_min_cap_factor():
    r = Resource(name="res")
    sink = Sink(name="sink", consumes=r, installed_capacity=4.0, min_capacity_factor=[0, 0.25])
    assert sink.minimum_at_timestep(0) == 0.0
    assert sink.minimum_at_timestep(1) == 1.0
    with pytest.raises(IndexError) as exc:
        sink.minimum_at_timestep(2)
    assert "outside of range for provided min_capacity_factor data" in str(exc.value)


@pytest.mark.unit()
@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        (
            {"installed_capacity": 3.0, "demand_profile": [3.0]},
            "'demand_profile' and 'installed_capacity'",
        ),
        (
            {"demand_profile": [4.0], "capacity_factor": [0.8]},
            "'demand_profile' and 'capacity_factor'",
        ),
        ({}, "Insufficient capacity information"),
        ({"produces": Resource(name="res")}, "produces"),
        ({"capacity_resource": Resource(name="res")}, "capacity_resource"),
        ({"demand_profile": [-5.0]}, "demand_profile"),
        ({"min_capacity_factor": [0.1], "demand_profile": [4.0]}, "min_capacity_factor"),
        (
            {"min_capacity_factor": [0.1], "min_demand_profile": [1.0], "installed_capacity": 2.0},
            "'min_capacity_factor' and 'min_demand_profile'",
        ),
        (
            {"demand_profile": [1.0], "min_demand_profile": [1.2]},
            "minimum activity value at timestep",
        ),
    ],
)
def test_sink_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="sink_bad")
    init_kwargs = {"name": "sink_bad", "consumes": r}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Sink(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_sink_min_demand_profile_and_fixed_flexibility_warns():
    r = Resource(name="res")
    with pytest.warns(UserWarning):
        Sink(
            name="sink", consumes=r, demand_profile=[3], min_demand_profile=[1], flexibility="fixed"
        )


@pytest.mark.unit()
def test_sink_with_explicit_capacity_resource():
    r = Resource(name="r")
    sink = Sink(name="sink", consumes=r, demand_profile=[1.0], capacity_resource=r)
    assert sink.capacity_resource is r


@pytest.mark.unit()
@pytest.mark.parametrize(
    "bad_kwargs, msg_substr",
    [
        ({"ramp_limit": 1.1}, "ramp_limit"),
        ({"ramp_freq": -1}, "ramp_freq"),
    ],
)
def test_converter_bad_ramp_values_raise(bad_kwargs, msg_substr):
    r1 = Resource(name="r1")
    r2 = Resource(name="r2")
    init_kwargs = {
        "name": "conv",
        "installed_capacity": 1.0,
        "consumes": [r1],
        "produces": [r2],
        "transfer_fn": RatioTransfer(input_resources={r1: 1.0}, output_resources={r2: 1.0}),
    }
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Converter(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
@pytest.mark.parametrize(
    "required_kwarg, msg_substr",
    [
        ("capacity_resource", "'capacity_resource' was not provided"),
        ("transfer_fn", "'transfer_fn' was not provided"),
    ],
)
def test_converter_missing_required_kwarg_raises(required_kwarg, msg_substr):
    r1 = Resource(name="r1")
    r2 = Resource(name="r2")
    init_kwargs = {
        "name": "conv",
        "installed_capacity": 1.0,
        "consumes": [r1],
        "produces": [r2],
        "capacity_resource": r1,
        "transfer_fn": RatioTransfer(input_resources={r1: 1.0}, output_resources={r2: 1.0}),
    }
    del init_kwargs[required_kwarg]
    with pytest.raises(ValueError) as exc:
        Converter(**init_kwargs)
    assert msg_substr in str(exc.value)


@pytest.mark.unit()
def test_converter_same_resource_raises():
    r = Resource(name="electricity")
    with pytest.raises(ValueError) as exc:
        Converter(
            name="conv",
            installed_capacity=15.0,
            consumes=[r],
            produces=[r],
            capacity_resource=r,
            transfer_fn=RatioTransfer(input_resources={r: 1.0}, output_resources={r: 1.0}),
        )
    assert "Resource 'electricity' found in both" in str(exc.value)


@pytest.mark.unit()
def test_storage_default_capacity_and_valid_ranges():
    r = Resource(name="stor_res")
    st = Storage(name="stor", installed_capacity=20.0, resource=r)
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
        ({"flexibility": "fixed"}, "flexibility"),
        ({"rte": 1.5}, "rte"),
        ({"max_charge_rate": -0.1}, "max_charge_rate"),
        ({"max_discharge_rate": 2.0}, "max_discharge_rate"),
        ({"initial_stored": -0.5}, "initial_stored"),
    ],
)
def test_storage_invalid_parameters_raise(bad_kwargs, msg_substr):
    r = Resource(name="stor_bad")
    init_kwargs = {"name": "stor_bad", "installed_capacity": 5.0, "resource": r}
    init_kwargs.update(bad_kwargs)
    with pytest.raises(ValueError) as exc:
        Storage(**init_kwargs)
    assert msg_substr in str(exc.value)
