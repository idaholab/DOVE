# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
"""
import math

import pytest

from dove import Converter, Cost, Resource, Revenue, Sink, Source, Storage, TransferTerm

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
