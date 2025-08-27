# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

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


@pytest.mark.unit()
def test_system_initialization_empty():
    sys = dc.System()
    assert isinstance(sys.components, list)
    assert sys.components == []
    assert isinstance(sys.resources, list)
    assert sys.resources == []


@pytest.mark.unit()
def test_system_summary(capsys):
    r = dc.Resource(name="res")
    src = dc.Source(name="src", installed_capacity=4.0, produces=r)
    sink = dc.Sink(name="sink", demand_profile=[2.0], consumes=r)
    storage = dc.Storage(name="storage", installed_capacity=1.0, resource=r)
    sys = dc.System(components=[src, sink, storage], resources=[r])

    sys.summary()  # Pytest will automatically capture stdout
    captured = capsys.readouterr()

    # Just some quick checks to make sure we're at least printing something relatively helpful
    assert "res" in captured.out
    assert "src" in captured.out
    assert "sink" in captured.out
    assert "storage" in captured.out


@pytest.mark.unit()
def test_system_setup(initialize_and_populate_system):
    """
    Tests __init__, add_component, add_resource, non_storage_comp_names, and storage_comp_names
    """
    r_w = dc.Resource(name="water")
    r_e = dc.Resource(name="electricity")

    src = dc.Source(
        name="src",
        installed_capacity=10.0,
        produces=r_w,
        cashflows=[dc.Cost(name="src_cf", alpha=2)],
    )
    sink = dc.Sink(
        name="sink",
        demand_profile=[3.0, 3.0, 3.0],
        consumes=r_e,
        cashflows=[dc.Cost(name="sink_cf", alpha=2)],
    )
    conv = dc.Converter(
        name="conv",
        installed_capacity=8.0,
        consumes=[r_w],
        produces=[r_e],
        capacity_resource=r_w,
        transfer_fn=dc.RatioTransfer(input_resources={r_w: 1.0}, output_resources={r_e: 1.0}),
        cashflows=[dc.Cost(name="conv_cf", alpha=2)],
    )
    storage = dc.Storage(
        name="storage",
        installed_capacity=2.0,
        resource=r_e,
        cashflows=[dc.Cost(name="storage_cf", alpha=2)],
    )

    # Automatically test with each setup methodology:
    # - Adding components and resources at initialization
    # - Adding components and resources after initialization
    # - Adding some components and resources at initialization and some after
    sys = initialize_and_populate_system(
        components=[src, sink, conv, storage],
        resources=[r_w, r_e],
        dispatch_window=[1, 2, 4],
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

    # Check dispatch window
    assert sys.dispatch_window == [1, 2, 4]


@pytest.mark.unit()
def test_adding_duplicate_component_name_raises_error(initialize_and_populate_system):
    r = dc.Resource(name="res")
    c1 = dc.Source(name="c", produces=r, installed_capacity=1.0, min_capacity_factor=[0.0])
    c2 = dc.Source(name="c", produces=r, installed_capacity=2.0, min_capacity_factor=[0.0])
    with pytest.raises(ValueError) as exc:
        sys = initialize_and_populate_system(resources=[r], components=[c1, c2])
        sys.solve("price_taker")
    assert "Component names must be unique" in str(exc.value)


@pytest.mark.unit()
def test_adding_duplicate_resource_name_raises_error(initialize_and_populate_system):
    r1 = dc.Resource(name="res")
    r2 = dc.Resource(name="res")
    c1 = dc.Source(name="c1", produces=r1, installed_capacity=1.0, min_capacity_factor=[0.0])
    c2 = dc.Source(name="c2", produces=r2, installed_capacity=2.0, min_capacity_factor=[0.0])
    with pytest.raises(ValueError) as exc:
        sys = initialize_and_populate_system(resources=[r1, r2], components=[c1, c2])
        sys.solve("price_taker")
    assert "Resource names must be unique" in str(exc.value)


@pytest.mark.unit()
@pytest.mark.parametrize(
    "kwargs, ts_name",
    [
        ({"installed_capacity": 1.0, "capacity_factor": [0.9]}, "capacity_factor"),
        ({"installed_capacity": 1.0, "min_capacity_factor": [0.5]}, "min_capacity_factor"),
        (
            {"installed_capacity": 1.0, "cashflows": [dc.Cost(name="cost", price_profile=[1.0])]},
            "price_profile",
        ),
        ({"demand_profile": [1.0]}, "demand_profile"),
        ({"demand_profile": [2.0, 2.0], "min_demand_profile": [1.0]}, "min_demand_profile"),
    ],
)
def test_insufficient_time_series_data_raises_error(kwargs, ts_name):
    r = dc.Resource(name="res")
    c = dc.Sink(name="sink", consumes=r, **kwargs)
    with pytest.raises(ValueError) as exc:
        sys = dc.System(components=[c], resources=[r], dispatch_window=[0, 1])
        sys.solve("price_taker")
    assert f"{ts_name} is of insufficient length" in str(exc.value)


@pytest.mark.unit()
def test_multiple_insufficient_time_series():
    r = dc.Resource(name="res")
    src = dc.Source(name="src", produces=r, installed_capacity=1.0, capacity_factor=[0.5])
    sink = dc.Sink(name="sink", consumes=r, installed_capacity=1.0, min_capacity_factor=[0.5])
    with pytest.raises(ValueError) as exc:
        sys = dc.System(components=[src, sink], resources=[r], dispatch_window=[0, 1])
        sys.solve("price_taker")
    assert "capacity_factor is of insufficient length" in str(exc.value)
    assert "min_capacity_factor is of insufficient length" in str(exc.value)


@pytest.mark.unit()
def test_solve_with_unknown_model_type_raises_error():
    r = dc.Resource(name="res")
    src = dc.Source(name="src", produces=r, installed_capacity=1.0)
    sink = dc.Sink(name="sink", consumes=r, demand_profile=[1.0])
    sys = dc.System(components=[src, sink], resources=[r])

    with pytest.raises(ValueError):
        sys.solve(model_type="quantum_mechanical")  # We don't have a quantum_mechanical model
