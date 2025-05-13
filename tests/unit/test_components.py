# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
"""
import math

import pytest

from dove import Converter, Cost, Resource, Revenue, Sink, Source, Storage, TransferTerm
from dataclasses import FrozenInstanceError

@pytest.fixture
def steam():
    return Resource("steam")

@pytest.fixture
def elec():
    return Resource("electricity")

def test_source_defaults_and_signs(steam):
    src = Source(
        name="injector",
        produces=steam,
        max_capacity=100.0,
    )
    assert src.capacity_resource is steam
    assert src.transfer_terms[0].coeff == +1.0

    src = Source(
        name="injector",
        produces=steam,
        max_capacity=100.0,
        transfer_terms=[TransferTerm(-1.0, {steam: 1})]
    )
    assert src.transfer_terms[0].coeff == +1.0

def test_resource_equality_and_immutability():
    r1 = Resource("water", unit="kg")
    r2 = Resource("water", unit="kg")
    assert r1 == r2
    with pytest.raises(FrozenInstanceError):
        r1.name = "steam"

def test_transfer_term_attributes(steam, elec):
    term = TransferTerm( coeff=2.5, exponent={steam: 2, elec: 1} )
    assert term.coeff == 2.5
    assert term.exponent == {steam: 2, elec: 1}

def test_cost_and_revenue_defaults_and_custom():
    c = Cost(
        name="capex",
        price_profile=[100, 200],
        alpha=0.5,
        dprime=0.8,
        scalex=1.2,
        price_is_levelized=True
    )
    assert c.name == "capex"
    assert c.price_profile == [100, 200]
    assert c.alpha == 0.5
    assert c.dprime == 0.8
    assert c.scalex == 1.2
    assert c.price_is_levelized is True
    assert c.sign == -1

    rev = Revenue(name="sales")
    assert rev.sign == +1
    # defaults
    assert rev.price_profile == []
    assert rev.alpha == 1.0
    assert rev.dprime == 1.0
    assert rev.scalex == 1.0
    assert rev.price_is_levelized is False
    assert rev.sign == +1

def test_sink_default_behavior(steam):
    s = Sink(name="cooler", consumes=steam)
    assert s.capacity_resource is steam
    assert len(s.transfer_terms) == 1
    term = s.transfer_terms[0]
    assert term.coeff == -1.0
    assert term.exponent == {steam: 1}

def test_converter_no_extras_same_resource(steam):
    # consumes == produces => no extras, capacity_resource auto-set
    conv = Converter(
        name="loop",
        consumes=[steam],
        produces=[steam]
    )
    assert conv.capacity_resource == steam
    # no transfer_terms so list is empty
    assert conv.transfer_terms == []

def test_converter_extras_without_capacity_fails(steam, elec):
    with pytest.raises(ValueError):
        Converter(
            name="bad1",
            consumes=[steam],
            produces=[elec]
        )

def test_converter_extras_with_capacity_but_no_terms_fails(steam, elec):
    with pytest.raises(ValueError):
        Converter(
            name="bad2",
            consumes=[steam],
            produces=[elec],
            capacity_resource=steam
        )

def test_converter_term_sign_adjustment(steam, elec):
    # capacity_resource in consumes => coeff becomes negative
    terms = [
        TransferTerm( coeff=4.0, exponent={steam:1} ),
        TransferTerm( coeff=-5.0, exponent={elec:1} )
    ]
    conv = Converter(
        name="conv",
        consumes=[steam],
        produces=[elec],
        capacity_resource=steam,
        transfer_terms=terms
    )
    # first term had steam exponent and steam in consumes => -abs(4.0)
    assert conv.transfer_terms[0].coeff == -4.0
    # second term has elec exponent (capacity_resource not in exponent) => unchanged
    assert conv.transfer_terms[1].coeff == +5.0

    # capacity_resource in produces => coeff becomes positive
    terms2 = [ TransferTerm(coeff=-7.0, exponent={elec:1}) ]
    conv2 = Converter(
        name="conv2",
        consumes=[steam],
        produces=[elec],
        capacity_resource=elec,
        transfer_terms=terms2
    )
    assert conv2.transfer_terms[0].coeff == +7.0

def test_storage_default_behavior(elec):
    st = Storage(name="tank", resource=elec)
    assert st.capacity_resource is elec
    # defaults
    assert st.rte == 1.0
    assert st.max_charge_rate == 1.0
    assert st.max_discharge_rate == 1.0
    assert st.initial_stored == 0.0
    assert st.periodic_level is True
