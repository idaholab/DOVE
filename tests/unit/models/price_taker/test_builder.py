# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import numpy as np
import pyomo.environ as pyo
import pytest

import dove.core as dc
from dove.models import BUILDER_REGISTRY


@pytest.fixture()
def create_example_system():
    """
    This establishes a simple system on which we can test the builder.
    It features multiple resources, multiple storage and non-storage components, and multiple timesteps.
    """

    ### Set up resources

    elec = dc.Resource("electricity")
    steam = dc.Resource("steam")

    resources = [elec, steam]

    ### Set up components

    # Non-storage
    steam_source = dc.Source(name="steam_source", produces=steam, max_capacity=1.0)

    steam_to_elec_converter = dc.Converter(
        name="steam_to_elec_converter",
        max_capacity=1.0,
        consumes=[steam],
        produces=[elec],
        capacity_resource=steam,
    )

    elec_sink = dc.Sink(name="elec_sink", consumes=elec, max_capacity=1.0)

    # Storage
    steam_storage = dc.Storage(name="steam_storage", resource=steam, max_capacity=1.0)
    elec_storage = dc.Storage(name="elec_storage", resource=elec, max_capacity=1.0)

    components = [steam_source, steam_to_elec_converter, elec_sink, steam_storage, elec_storage]

    ### Set up times
    time_index = np.array([0, 1])

    ### Create and return system
    sys = dc.System(components, resources, time_index)
    return sys


@pytest.fixture()
def builder_setup(create_example_system):
    price_taker_builder_cls = BUILDER_REGISTRY["price_taker"]
    price_taker_builder = price_taker_builder_cls(create_example_system)
    price_taker_builder.model = pyo.ConcreteModel()
    price_taker_builder.model.system = price_taker_builder.system

    return price_taker_builder


def test_add_sets(builder_setup):
    # Call method under test
    builder_setup._add_sets()

    # Find the actual pyo.Set variables and extract data as tuples of strings

    m = builder_setup.model

    actual_non_storage = m.NON_STORAGE.data()
    actual_storage = m.STORAGE.data()
    actual_r = m.R.data()
    actual_t = m.T.data()

    # Find the expected values for the sets as lists of strings

    sys = builder_setup.system

    expected_non_storage = sys.non_storage_comp_names
    expected_storage = sys.storage_comp_names
    expected_r = [r.name for r in sys.resources]
    expected_t = sys.time_index

    # Convert both actual (tuple) and expected (list) values to sets and check that they're the same

    assert set(actual_non_storage) == set(expected_non_storage)
    assert set(actual_storage) == set(expected_storage)
    assert set(actual_r) == set(expected_r)
    assert set(actual_t) == set(expected_t)
