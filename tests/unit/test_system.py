# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import numpy as np
import pytest

import dove.core as dc

### FIXTURE DEFINITIONS


@pytest.fixture(
    params=[
        "populate_at_initialization",
        "populate_after_initialization",
        "populate_some_at_intialization",
    ]
)
def initialize_and_populate_system(request):
    def _initialize_and_populate_system(components, resources, **kw):
        if request.param == "populate_at_initialization":
            sys = dc.System(components=components, resources=resources, **kw)
        elif request.param == "populate_after_initialization":
            sys = dc.System(**kw)
            for res in resources:
                sys.add_resource(res)
            for comp in components:
                sys.add_component(comp)
        else:
            # Populate some at initialization
            sys = dc.System(components=components[:1], resources=resources[:1], **kw)

            # Populate the rest after
            for res in resources[1:]:
                sys.add_resource(res)
            for comp in components[1:]:
                sys.add_component(comp)

        return sys

    return _initialize_and_populate_system


### TEST DEFINITIONS


def test_system_initialization_empty():
    sys = dc.System()
    assert isinstance(sys.components, list)
    assert sys.components == []
    assert isinstance(sys.resources, list)
    assert sys.resources == []


def test_system_summary(capsys):
    r = dc.Resource(name="res")
    src = dc.Source(name="src", max_capacity=4.0, produces=r)
    sink = dc.Sink(name="sink", max_capacity=2.0, consumes=r)
    storage = dc.Storage(name="storage", max_capacity=1.0, resource=r)
    sys = dc.System(components=[src, sink, storage], resources=[r])

    sys.summary()  # Pytest will automatically capture stdout
    captured = capsys.readouterr()

    # Just some quick checks to make sure we're at least printing something relatively helpful
    assert "res" in captured.out
    assert "src" in captured.out
    assert "sink" in captured.out
    assert "storage" in captured.out


def test_system_setup(initialize_and_populate_system):
    """
    Tests __init__, add_component, add_resource, non_storage_comp_names, and storage_comp_names
    """
    r_w = dc.Resource(name="water")
    r_e = dc.Resource(name="electricity")

    src = dc.Source(
        name="src",
        max_capacity=10.0,
        produces=r_w,
        cashflows=[dc.Cost(name="src_cf", alpha=2)],
    )
    sink = dc.Sink(
        name="sink",
        max_capacity=5.0,
        consumes=r_e,
        cashflows=[dc.Cost(name="sink_cf", alpha=2)],
    )
    conv = dc.Converter(
        name="conv",
        max_capacity=8.0,
        consumes=[r_w],
        produces=[r_e],
        capacity_resource=r_w,
        transfer_fn=dc.RatioTransfer(input_res=r_w, output_res=r_e, ratio=1.0),
        cashflows=[dc.Cost(name="conv_cf", alpha=2)],
    )
    storage = dc.Storage(
        name="storage",
        max_capacity=2.0,
        resource=r_e,
        cashflows=[dc.Cost(name="storage_cf", alpha=2)],
    )

    # Automatically test with each setup methodology:
    # - Adding components and resources at initialization
    # - Adding components and resources after initialization
    # - Adding some components and resources at initialization and some after
    sys = initialize_and_populate_system(
        components=[src, sink, conv, storage], resources=[r_w, r_e], time_index=np.array([1, 2, 4])
    )

    # Check component list
    assert src in sys.components
    assert sink in sys.components
    assert conv in sys.components
    assert storage in sys.components

    # Check component map
    assert sys.comp_map["src"] is src
    assert sys.comp_map["sink"] is sink
    assert sys.comp_map["conv"] is conv
    assert sys.comp_map["storage"] is storage

    # Check storage and non-storage component name lists
    assert "src" in sys.non_storage_comp_names
    assert "sink" in sys.non_storage_comp_names
    assert "conv" in sys.non_storage_comp_names
    assert "storage" in sys.storage_comp_names

    # Check resource list
    assert r_w in sys.resources
    assert r_e in sys.resources

    # Check resource map
    assert sys.res_map["water"] is r_w
    assert sys.res_map["electricity"] is r_e

    # Check time index
    assert (sys.time_index == np.array([1, 2, 4])).all()

    # Check that time series were normalized
    # NOT a thorough test of normalization; just checking that it was called for each component
    assert src.cashflows[0].price_profile is not None
    assert len(src.cashflows[0].price_profile) == 3

    assert sink.cashflows[0].price_profile is not None
    assert len(sink.cashflows[0].price_profile) == 3

    assert conv.cashflows[0].price_profile is not None
    assert len(conv.cashflows[0].price_profile) == 3

    assert storage.cashflows[0].price_profile is not None
    assert len(storage.cashflows[0].price_profile) == 3


def test_adding_non_component_to_components_raises_error(initialize_and_populate_system):
    res = dc.Resource(name="res")
    c1 = dc.Source(name="c1", produces=res, max_capacity=1.0)
    with pytest.raises(TypeError):
        initialize_and_populate_system(
            resources=[res],
            components=[c1, "c2"],  # c2 is a string, not a Component
        )


def test_adding_non_resource_to_resources_raises_error(initialize_and_populate_system):
    r1 = dc.Resource(name="r1")
    c = dc.Source(name="c1", produces=r1, max_capacity=1.0)
    with pytest.raises(TypeError):
        initialize_and_populate_system(
            resources=[r1, "r2"],
            components=[c],  # r2 is a string, not a Resource
        )


def test_adding_duplicate_component_name_raises_error(initialize_and_populate_system):
    r = dc.Resource(name="res")
    c1 = dc.Source(name="c", produces=r, max_capacity=1.0, min_capacity=0.0, profile=[0.1])
    c2 = dc.Source(name="c", produces=r, max_capacity=2.0, min_capacity=0.0, profile=[0.2])
    with pytest.raises(ValueError):
        initialize_and_populate_system(resources=[r], components=[c1, c2])


def test_adding_duplicate_resource_name_raises_error(initialize_and_populate_system):
    r1 = dc.Resource(name="res")
    r2 = dc.Resource(name="res")
    c1 = dc.Source(name="c1", produces=r1, max_capacity=1.0, min_capacity=0.0, profile=[0.1])
    c2 = dc.Source(name="c2", produces=r2, max_capacity=2.0, min_capacity=0.0, profile=[0.2])
    with pytest.raises(ValueError):
        initialize_and_populate_system(resources=[r1, r2], components=[c1, c2])


def test_inconsistent_comp_profile_length_raises_error(initialize_and_populate_system):
    r = dc.Resource(name="res")
    c = dc.Source(name="c", produces=r, max_capacity=1.0, min_capacity=0.0, profile=[0.1])
    with pytest.raises(ValueError):
        initialize_and_populate_system(resources=[r], components=[c], time_index=[1, 2])


def test_inconsistent_cf_price_profile_length_raises_error(initialize_and_populate_system):
    r = dc.Resource(name="res")
    c = dc.Source(
        name="c",
        produces=r,
        max_capacity=1.0,
        min_capacity=0.0,
        profile=[0.1, 0.2],
        cashflows=[dc.Cost(name="cf", price_profile=np.array([2]))],
    )
    with pytest.raises(ValueError):
        initialize_and_populate_system(resources=[r], components=[c], time_index=[1, 2])


def test_solve_with_unknown_model_type_raises_error():
    r = dc.Resource(name="res")
    src = dc.Source(name="src", produces=r, max_capacity=1.0)
    sink = dc.Sink(name="sink", consumes=r, max_capacity=1.0)
    sys = dc.System(components=[src, sink], resources=[r])

    with pytest.raises(ValueError):
        sys.solve(model_type="quantum_mechanical")  # We don't have a quantum_mechanical model


def test_normalize_time_series():
    r1 = dc.Resource(name="r1")
    r2 = dc.Resource(name="r2")

    cap_factor_comp = dc.Source(
        name="src",
        produces=r1,
        max_capacity=10,
        profile=[0.5, 1.0, 0.5],
        capacity_factor=True,
        cashflows=[dc.Cost(name="src_cost", alpha=2)],  # No price profile
    )
    fixed_flex_comp = dc.Sink(
        name="sink",
        consumes=r2,
        max_capacity=4,
        flexibility="fixed",
        cashflows=[
            dc.Revenue(
                name="sink_revenue",
                alpha=2,
                price_profile=np.array([2, 3, 4]),  # Price profile and alpha
            )
        ],
    )
    cap_factor_and_fixed_flex_comp = dc.Converter(
        name="conv",
        consumes=[r1],
        produces=[r2],
        max_capacity=5,
        capacity_resource=r1,
        profile=[0.8, 0.6, 0.6],
        capacity_factor=True,
        flexibility="fixed",
        transfer_fn=dc.RatioTransfer(input_res=r1, output_res=r2, ratio=0.5),
    )

    # Constructing the system should automatically normalize components
    sys = dc.System(
        components=[cap_factor_comp, fixed_flex_comp],  # Only two of the components
        resources=[r1, r2],
        time_index=np.array([1, 2, 3]),
    )

    # Adding a component should automatically normalize it also
    sys.add_component(cap_factor_and_fixed_flex_comp)

    # Check component profiles
    assert (sys.comp_map["src"].profile == np.array([5.0, 10.0, 5.0])).all()
    assert (sys.comp_map["sink"].profile == np.array([4.0, 4.0, 4.0])).all()
    assert (sys.comp_map["conv"].profile == np.array([4.0, 3.0, 3.0])).all()

    # Check cashflow price profiles
    assert (sys.comp_map["src"].cashflows[0].price_profile == np.array([2, 2, 2])).all()
    assert (sys.comp_map["sink"].cashflows[0].price_profile == np.array([4, 6, 8])).all()
