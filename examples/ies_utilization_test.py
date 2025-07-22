# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED

"""
This script examines the utilization of a hydrogen-based IES relative
to the ratio of installed solar to natural gas in the system.
"""

import numpy as np
import pandas as pd

import dove.core as dc


def create_system(solar_capacity_scale: float):
    # IMPORTANT: all data in this example is fictional and should not be used for analysis purposes

    # Read in NYISO data
    nyiso_data = pd.read_csv("NYISO_data_8760.csv")

    # Time-series inputs
    solar_cap_factor_profile = nyiso_data["SOLAR"].values
    solar_capacity_profile = solar_cap_factor_profile * solar_capacity_scale

    GRID_SCALE = 1.0
    grid_profile = GRID_SCALE * nyiso_data["TOTALLOAD"]

    # Set up resources
    steam = dc.Resource("steam")
    elec = dc.Resource("elec")
    h2 = dc.Resource("h2")

    # Set up components
    lwr = dc.Source(
        name="lwr",
        produces=steam,
        max_capacity_profile=np.full(len(grid_profile), 25),
    )

    steam_turbine = dc.Converter(
        name="steam_turbine",
        consumes=[steam],
        produces=[elec],
        capacity_resource=steam,
        max_capacity_profile=np.full(len(grid_profile), 25),
        transfer_fn=dc.RatioTransfer(input_resources={steam: 1.0}, output_resources={elec: 0.34}),
    )

    solar = dc.Source(
        name="solar",
        produces=elec,
        max_capacity_profile=solar_capacity_profile,
    )

    ng = dc.Source(
        name="natural_gas_plant",
        produces=elec,
        max_capacity_profile=np.full(len(grid_profile), 20 - np.average(solar_capacity_profile)),
        cashflows=[
            dc.Cost(name="ng_vom", alpha=5e3),
            dc.Cost(name="ng_fuel_cost", alpha=37e3),
        ],
    )

    htse = dc.Converter(
        name="htse",
        consumes=[steam, elec],
        produces=[h2],
        max_capacity_profile=np.full(len(grid_profile), 2.0),
        capacity_resource=elec,
        transfer_fn=dc.RatioTransfer(
            input_resources={steam: 0.094, elec: 0.538}, output_resources={h2: 14623}
        ),
        cashflows=[dc.Cost(name="htse_vom", alpha=2.85e-7)],  # $ per kg h2 per hour
    )

    h2_storage = dc.Storage(
        name="h2_storage",
        resource=h2,
        max_capacity_profile=np.full(len(grid_profile), 1.5e5),
    )

    h2_turbine = dc.Converter(
        name="h2_turbine",
        consumes=[h2],
        produces=[elec],
        max_capacity_profile=np.full(len(grid_profile), 2.0),
        capacity_resource=elec,
        transfer_fn=dc.RatioTransfer(input_resources={h2: 1.0}, output_resources={elec: 1.342e-5}),
        cashflows=[dc.Cost(name="h2_turbine_vom", alpha=2e3)],
    )

    elec_import = dc.Source(
        name="import",
        produces=elec,
        max_capacity_profile=np.full(len(grid_profile), 30),
        cashflows=[dc.Cost(name="import_cost", alpha=10e6)],
    )

    elec_export = dc.Sink(
        name="export",
        consumes=elec,
        max_capacity_profile=np.full(len(grid_profile), 30),
        cashflows=[dc.Cost(name="export_cost", alpha=10e6)],
    )

    grid = dc.Sink(
        name="grid",
        consumes=elec,
        max_capacity_profile=grid_profile,
        flexibility="fixed",
    )

    # Create and solve system
    sys = dc.System(
        components=[
            lwr,
            steam_turbine,
            solar,
            ng,
            htse,
            h2_storage,
            h2_turbine,
            elec_import,
            elec_export,
            grid,
        ],
        resources=[steam, elec, h2],
        time_index=list(range(len(grid_profile))),
    )
    results = sys.solve("price_taker")
    print("completed run")

    return results


def run_test():
    results = {}
    for solar_cap_multiplier in range(4, 20, 4):
        results[f"{solar_cap_multiplier}_GWe_solar_capacity"] = create_system(solar_cap_multiplier)

    # plot htse utilization changes with solar capacity
    htse_utilization = {}
    objective = {}
    for case, result in results.items():
        htse_utilization[case] = np.sum(result["htse_h2_produces"].values)
        objective[case] = result["objective"].values[0]

    print(htse_utilization)
    print(objective)


if __name__ == "__main__":
    run_test()
