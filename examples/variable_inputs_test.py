# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED

"""
This script demonstrates a case where input time series vary greatly
"""

import numpy as np
from check_constraints_working import (
    capacity_working,
    max_charge_rate_working,
    max_discharge_rate_working,
    periodic_storage_working,
    ramp_freq_working,
    ramp_limit_working,
    rte_working,
)

import dove.core as dc


def run_test():
    # Set up time series data

    # Electricity demand profile with high variability
    elec_demand_profile = np.array(
        [
            160,
            140,
            120,
            100,
            80,
            60,
            40,
            20,
            40,
            80,
            140,
            200,
            260,
            320,
            360,
            400,
            380,
            340,
            300,
            260,
        ]
    )

    # Scale electricity price on demand
    scale = 1.0
    elec_price_profile = np.multiply(elec_demand_profile, scale)

    # Super volatile wind profile
    wind_capacity_factor_profile = np.array(
        [
            0.75,
            0.00,
            0.43,
            0.68,
            0.00,
            0.19,
            0.57,
            0.00,
            0.81,
            0.00,
            0.34,
            0.27,
            0.49,
            0.00,
            0.62,
            0.55,
            0.23,
            0.78,
            0.11,
            0.30,
        ]
    )

    # Smooth solar profile, but only producing half the time
    solar_capacity_profile = np.array(
        [
            0,
            0,
            0,
            0,
            0,
            15,
            35,
            60,
            90,
            100,
            100,
            90,
            60,
            35,
            15,
            0,
            0,
            0,
            0,
            0,
        ]
    )
    # Convert data to installed cap and cap factor
    solar_max_capacity = np.max(solar_capacity_profile)
    solar_cap_factor_profile = solar_capacity_profile / solar_max_capacity

    # Set up resources
    electricity = dc.Resource(name="electricity")
    steam = dc.Resource(name="steam")

    wind = dc.Source(
        name="wind",
        produces=electricity,
        capacity_factor=wind_capacity_factor_profile,
        installed_capacity=100,
    )

    solar = dc.Source(
        name="solar",
        produces=electricity,
        installed_capacity=solar_max_capacity,
        capacity_factor=solar_cap_factor_profile,
    )

    smr = dc.Source(
        name="smr",
        produces=steam,
        installed_capacity=200,
        cashflows=[dc.Cost(name="vom", alpha=2)],
    )

    generator = dc.Converter(
        name="generator",
        consumes=[steam],
        produces=[electricity],
        installed_capacity=300,
        capacity_resource=steam,
        ramp_limit=0.4,
        ramp_freq=2,
        transfer_fn=dc.RatioTransfer(
            input_resources={steam: 1.0}, output_resources={electricity: 0.9}
        ),
    )

    steam_storage = dc.Storage(
        name="steam_storage",
        resource=steam,
        max_charge_rate=0.4,
        max_discharge_rate=0.4,
        rte=0.9,
        installed_capacity=300,
        initial_stored=0.5,
    )

    battery = dc.Storage(
        name="battery",
        resource=electricity,
        max_charge_rate=0.75,
        max_discharge_rate=0.75,
        rte=0.8,
        installed_capacity=100,
        initial_stored=0.5,
    )

    grid = dc.Sink(
        name="grid",
        consumes=electricity,
        demand_profile=elec_demand_profile,
        flexibility="flex",
        cashflows=[dc.Revenue(name="elec_sales", price_profile=elec_price_profile)],
    )

    sys = dc.System(
        components=[wind, solar, smr, generator, steam_storage, battery, grid],
        resources=[steam, electricity],
        dispatch_window=np.arange(0, 20),
    )

    results = sys.solve("price_taker")

    with open("variable_inputs_test_results.csv", "w") as f:
        f.write(results.to_csv())  # Easiest way to view the results is as a csv
    print(results)

    # Confirm that constraints are not being violated
    capacity_working(sys, results, "smr", "smr_steam_produces")
    capacity_working(sys, results, "battery", "battery_SOC")
    capacity_working(sys, results, "wind", "wind_electricity_produces")

    ramp_limit_working(sys, results, "generator", "generator_steam_consumes")
    ramp_freq_working(sys, results, "generator", "generator_steam_consumes")

    max_charge_rate_working(sys, results, "battery")
    max_discharge_rate_working(sys, results, "battery")
    rte_working(sys, results, "battery")
    periodic_storage_working(sys, results, "battery")


if __name__ == "__main__":
    run_test()
