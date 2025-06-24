import numpy as np
import pandas as pd
import pytest

import dove.core as dc


@pytest.fixture()
def generic_system_setup():
    def _generic_system_setup(
        source_cfs=None, converter_cfs=None, storage_cfs=None, sink_cfs=None, times=1
    ):
        # Creates a generic system that can be used for simple tests on economics edge cases

        # Resources
        steam = dc.Resource(name="steam")
        electricity = dc.Resource(name="electricity")

        # Components
        src_init_kwargs = {
            "name": "steam_source",
            "produces": steam,
            "max_capacity_profile": np.full(times, 100),
            "min_capacity_profile": np.full(times, 50),  # Force the system to do something at least
        }
        if source_cfs:
            src_init_kwargs.update({"cashflows": source_cfs})
        source = dc.Source(**src_init_kwargs)

        conv_init_kwargs = {
            "name": "steam_to_elec_converter",
            "consumes": [steam],
            "produces": [electricity],
            "max_capacity_profile": np.full(times, 100),
            "capacity_resource": steam,
            "transfer_fn": dc.RatioTransfer(input_res=steam, output_res=electricity, ratio=0.5),
        }
        if converter_cfs:
            conv_init_kwargs.update({"cashflows": converter_cfs})
        converter = dc.Converter(**conv_init_kwargs)

        stor_init_kwargs = {
            "name": "elec_storage",
            "resource": electricity,
            "max_capacity_profile": np.full(times, 40),
            "rte": 0.9,
            "max_charge_rate": 0.5,
            "max_discharge_rate": 0.5,
        }
        if storage_cfs:
            stor_init_kwargs.update({"cashflows": storage_cfs})
        storage = dc.Storage(**stor_init_kwargs)

        sink_init_kwargs = {
            "name": "elec_sink",
            "consumes": electricity,
            "max_capacity_profile": np.full(times, 100),
        }
        if sink_cfs:
            sink_init_kwargs.update({"cashflows": sink_cfs})
        sink = dc.Sink(**sink_init_kwargs)

        # Times
        time_index = np.arange(0, times)

        # System
        sys = dc.System(
            components=[source, converter, storage, sink],
            resources=[steam, electricity],
            time_index=time_index,
        )

        return sys

    return _generic_system_setup


@pytest.mark.integration()
def test_with_no_cfs(generic_system_setup):
    # Create and solve system
    sys = generic_system_setup(source_cfs=[], sink_cfs=[])
    results = sys.solve("price_taker")
    print(results)

    # Check results
    expected = pd.DataFrame(
        {
            "steam_source_steam_produces": [50.0],
            "steam_to_elec_converter_electricity_produces": [25.0],
            "steam_to_elec_converter_steam_consumes": [-50.0],
            "elec_storage_SOC": [0.0],
            "elec_storage_charge": [0.0],
            "elec_storage_discharge": [0.0],
            "elec_sink_electricity_consumes": [-25.0],
            "objective": [0],
        }
    )

    pd.testing.assert_frame_equal(results, expected, check_like=True, atol=1e-8)


@pytest.mark.integration()
def test_with_costs_only(generic_system_setup):
    times = 4

    # Set up cashflows
    source_cost = dc.Cost(name="steam_source_fuel_cost", price_profile=np.arange(1 + times, 1))
    sink_cost = dc.Cost(name="export_cost", alpha=1)

    # Create and solve system
    sys = generic_system_setup(source_cfs=[source_cost], sink_cfs=[sink_cost], times=times)
    results = sys.solve("price_taker")
    print(results)

    # Check results
    expected = pd.DataFrame(
        {
            "steam_source_steam_produces": [50.0, 50.0, 50.0, 50.0],
            "steam_to_elec_converter_electricity_produces": [25.0, 25.0, 25.0, 25.0],
            "steam_to_elec_converter_steam_consumes": [-50.0, -50.0, -50.0, -50.0],
            "elec_storage_SOC": [0.0, 0.0, 2.108185, 0.0],
            "elec_storage_charge": [20.0, 20.0, 20.0, 20.0],
            "elec_storage_discharge": [18.0, 18, 16.0, 20.0],
            "elec_sink_electricity_consumes": [-23.0, -23.0, -21.0, -25.0],
            "objective": [-292.0, -292.0, -292.0, -292.0],
        }
    )

    pd.testing.assert_frame_equal(results, expected, check_like=True, atol=1e-8)


@pytest.mark.integration()
def test_with_revenues_only(generic_system_setup):
    times = 4

    # Set up cashflow
    elec_sales = dc.Revenue(name="elec_sales", price_profile=np.array([1, 1, 3, 1]))

    # Create and solve system
    sys = generic_system_setup(sink_cfs=[elec_sales], times=times)
    results = sys.solve("price_taker")
    print(results)

    # Check results
    expected = pd.DataFrame(
        {
            "steam_source_steam_produces": [100.0, 100.0, 100.0, 100.0],
            "steam_to_elec_converter_electricity_produces": [50.0, 50.0, 50.0, 50.0],
            "steam_to_elec_converter_steam_consumes": [-100.0, -100.0, -100.0, -100.0],
            "elec_storage_SOC": [2.108185, 21.081851, 0.0, 0.0],
            "elec_storage_charge": [2.222222, 20.0, 0.0, 0.0],
            "elec_storage_discharge": [0.0, 0.0, 20.0, 0.0],
            "elec_sink_electricity_consumes": [-47.777778, -30.0, -70.0, -50.0],
            "objective": [337.777778, 337.777778, 337.777778, 337.777778],
        }
    )

    pd.testing.assert_frame_equal(results, expected, check_like=True, atol=1e-8)


@pytest.mark.integration()
def test_cashflow_combos(generic_system_setup):
    times = 4

    # Set up cashflows
    source1_fuel_cost = dc.Cost(name="source1_fuel_cost", price_profile=[1, 3, 2, 1])
    source1_input_elec_cost = dc.Cost(name="source1_input_elec_cost", alpha=2)

    source2_fuel_cost = dc.Cost(name="source2_fuel_cost", price_profile=[3, 4, 3, 5])
    source2_revenue = dc.Revenue(
        name="source2_revenue", alpha=1
    )  # Not sure what practical scenario this would refer to

    sink_elec_sales_regular = dc.Revenue(
        name="sink1_elec_sales_regular", price_profile=[10, 10.5, 11, 11.5]
    )
    sink_elec_sales_spike = dc.Revenue(name="sink1_elec_sales_spike", price_profile=[0, 10, 0, 0])

    # Create system, add extra component, and solve
    sys = generic_system_setup(
        source_cfs=[source1_fuel_cost, source1_input_elec_cost],
        sink_cfs=[sink_elec_sales_regular, sink_elec_sales_spike],
        times=times,
    )

    sys.add_component(
        dc.Source(
            name="elec_source",
            produces=sys.res_map["electricity"],
            max_capacity_profile=np.full(times, 20),
            min_capacity_profile=np.full(times, 10),
            cashflows=[source2_fuel_cost, source2_revenue],
        )
    )
    results = sys.solve()
    print(results)

    # Check results
    expected = pd.DataFrame(
        {
            "steam_source_steam_produces": [100.0, 100.0, 100.0, 100.0],
            "elec_source_electricity_produces": [20.0, 20.0, 20.0, 20.0],
            "steam_to_elec_converter_electricity_produces": [50.0, 50.0, 50.0, 50.0],
            "steam_to_elec_converter_steam_consumes": [-100.0, -100.0, -100.0, -100.0],
            "elec_storage_SOC": [18.973666, 0.0, 0.0, 0.0],
            "elec_storage_charge": [20.0, 0.0, 0.0, 0.0],
            "elec_storage_discharge": [0.0, 18.0, 0.0, 0.0],
            "elec_sink_electricity_consumes": [-50.0, -88.0, -70.0, -70.0],
            "objective": [2159.0, 2159.0, 2159.0, 2159.0],
        }
    )

    pd.testing.assert_frame_equal(results, expected, check_like=True, atol=1e-8)
