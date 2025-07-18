#!/usr/bin/env python
# Copyright 2024, Battelle Energy Alliance, LLC
"""
Test script for ramping constraints in DOVE.

This script creates a simple system with ramping-constrained components
and tests the implementation of both ramp rate and ramp frequency constraints.
"""

import numpy as np

from dove.core import (
    Converter,
    Cost,
    RatioTransfer,
    Resource,
    Sink,
    Source,
    System,
)

# Constants
BOP_CAPACITY = 200
RAMP_LIMIT = 0.5
RAMP_FREQ = 2


def create_test_system(with_ramping=True):
    """
    Create a test system with ramping-constrained components.

    Parameters
    ----------
    with_ramping : bool, default=True
        Whether to include ramping constraints in the system

    Returns
    -------
    System
        A DOVE System object configured for ramping test
    """
    # Time periods - 24 hours
    hours = list(range(11))

    # Create resources
    steam = Resource("steam")
    electricity = Resource("electricity")

    # Time Series Grid Demand

    npp = Source(
        name="npp",
        produces=steam,
        max_capacity_profile=np.full(len(hours), 700),
    )

    npp_bop = Converter(
        name="npp_bop",
        consumes=[steam],
        produces=[electricity],
        max_capacity_profile=np.full(len(hours), BOP_CAPACITY),
        capacity_resource=electricity,
        transfer_fn=RatioTransfer(
            input_resources={steam: 1.0}, output_resources={electricity: 0.333}
        ),
    )

    # Apply ramping constraints if requested
    if with_ramping:
        # Generator can ramp 50% of capacity per time period
        npp_bop.ramp_limit = RAMP_LIMIT
        npp_bop.ramp_freq = RAMP_FREQ

    ngcc = Source(
        name="ngcc",
        produces=electricity,
        max_capacity_profile=np.full(len(hours), 400),
        cashflows=[Cost(name="ngcc_cost", alpha=0.3)],
    )

    # Create a load with varying demand
    # Demand profile with morning and evening peaks
    demand_profile = np.array([1e-5, 200, 200, 300, 100, 100, 1e-5, 200, 400, 200, 1e-5])

    grid = Sink(
        name="grid", consumes=electricity, max_capacity_profile=demand_profile, flexibility="fixed"
    )

    # Create and populate the system
    system = System(time_index=hours)
    system.add_resource(electricity)
    system.add_resource(steam)
    system.add_component(npp)
    system.add_component(npp_bop)
    system.add_component(ngcc)
    system.add_component(grid)

    return system


def run_test():
    """
    Run the ramping test and analyze results.
    """
    # Create systems with and without ramping constraints
    system_with_ramping = create_test_system(with_ramping=True)
    system_without_ramping = create_test_system(with_ramping=False)

    # Solve both systems
    results_with_ramping = system_with_ramping.solve(model_type="price_taker")
    results_without_ramping = system_without_ramping.solve(model_type="price_taker")

    print(results_with_ramping)

    # Extract npp_bop dispatch profiles for comparison
    gen_with_ramping = results_with_ramping.loc[:, "npp_bop_electricity_produces"].values
    gen_without_ramping = results_without_ramping.loc[:, "npp_bop_electricity_produces"].values

    # Calculate ramp rates
    ramp_rates_with = np.abs(np.diff(gen_with_ramping))
    ramp_rates_without = np.abs(np.diff(gen_without_ramping))

    # Check if ramp limit constraint is working
    max_allowed_ramp = RAMP_LIMIT * BOP_CAPACITY  # 50% of 200 MW capacity
    print(f"Maximum allowed ramp rate: {max_allowed_ramp:.2f} MW")
    print(f"Max ramp rate with constraints: {np.max(ramp_rates_with):.2f} MW")
    print(f"Max ramp rate without constraints: {np.max(ramp_rates_without):.2f} MW")

    # Count ramp events
    # Define a significant ramp as >5% of capacity
    ramp_threshold = 0.05 * BOP_CAPACITY
    ramp_events_with = ramp_rates_with > ramp_threshold
    ramp_events_without = ramp_rates_without > ramp_threshold

    max_ramps_per_window = []
    for i in range(len(ramp_events_with) - RAMP_FREQ + 1):
        window = ramp_events_with[i : i + 2]
        max_ramps_per_window.append(np.sum(window))

    print(
        f"Maximum ramps in any {RAMP_FREQ}-hour window with constraints: {np.max(max_ramps_per_window)}"
    )
    print(f"Total ramp events with constraints: {np.sum(ramp_events_with)}")
    print(f"Total ramp events without constraints: {np.sum(ramp_events_without)}")

    # Show a summary of results
    print("\nTest Summary:")
    if np.all(ramp_rates_with <= max_allowed_ramp + 1e-6):
        print("✅ Ramp rate limit constraint working correctly!")
    else:
        print("❌ Ramp rate limit constraint violated!")

    if np.max(max_ramps_per_window) <= 1:
        print("✅ Ramp frequency constraint working correctly!")
    else:
        print("❌ Ramp frequency constraint violated!")

    cost_with_ramping = -results_with_ramping["objective"].values[0]
    cost_without_ramping = -results_without_ramping["objective"].values[0]
    cost_diff = np.abs(cost_with_ramping - cost_without_ramping)
    print(f"\nTotal system cost with ramping constraints: ${cost_with_ramping:.2f}")
    print(f"Total system cost without ramping constraints: ${cost_without_ramping:.2f}")
    print(f"Cost increase due to ramping constraints: ${cost_diff:.2f}")


if __name__ == "__main__":
    run_test()
