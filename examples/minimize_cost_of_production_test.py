# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED

"""
This script demonstrates a case where electricity demand must be satisfied at minimum cost
"""

from check_constraints_working import (
    capacity_working,
    fixed_flexibility_working,
)

import dove.core as dc


def run_test():
    # Set up resources
    elec_near = dc.Resource(name="elec_near")
    elec_far = dc.Resource(name="elec_far")
    elec_farther = dc.Resource(name="elec_farther")

    # Set up components
    elec_plant_near = dc.Source(
        name="elec_plant_near",
        produces=elec_near,
        installed_capacity=100,
        cashflows=[dc.Cost("near_plant_om", price_profile=[4, 4, 8, 12, 8, 12])],
    )

    elec_plant_far = dc.Source(
        name="elec_plant_far",
        produces=elec_far,
        installed_capacity=100,
        cashflows=[dc.Cost("far_plant_om", price_profile=[6, 9, 3, 3, 9, 6])],
    )

    elec_plant_farther = dc.Source(
        name="elec_plant_farther",
        produces=elec_farther,
        installed_capacity=100,
        cashflows=[dc.Cost("farther_plant_om", price_profile=[6, 4, 6, 4, 2, 2])],
    )

    transmission_from_far = dc.Converter(
        name="transmission_far",
        consumes=[elec_far],
        produces=[elec_near],
        capacity_resource=elec_far,
        installed_capacity=200,
        transfer_fn=dc.RatioTransfer(
            input_resources={elec_far: 1.0}, output_resources={elec_near: 0.75}
        ),
    )

    transmission_from_farther = dc.Converter(
        name="transmission_farther",
        consumes=[elec_farther],
        produces=[elec_near],
        capacity_resource=elec_farther,
        installed_capacity=200,
        transfer_fn=dc.RatioTransfer(
            input_resources={elec_farther: 1.0}, output_resources={elec_near: 0.5}
        ),
    )

    elec_demand = dc.Sink(
        name="elec_demand",
        consumes=elec_near,
        installed_capacity=120,
        flexibility="fixed",
    )

    # Set up and solve system
    sys = dc.System(
        components=[
            elec_plant_near,
            elec_plant_far,
            elec_plant_farther,
            transmission_from_far,
            transmission_from_farther,
            elec_demand,
        ],
        resources=[elec_near, elec_far, elec_farther],
        dispatch_window=[0, 1, 2, 3, 4, 5],
    )
    results = sys.solve("price_taker")

    with open("minimize_cost_of_production_test_results.csv", "w") as f:
        f.write(results.to_csv())  # Easiest way to view the results is as a csv
    print(results)

    # Confirm that constraints are not being violated
    capacity_working(sys, results, "elec_plant_near", "elec_plant_near_elec_near_produces")
    capacity_working(sys, results, "elec_plant_far", "elec_plant_far_elec_far_produces")
    capacity_working(sys, results, "elec_plant_farther", "elec_plant_farther_elec_farther_produces")
    fixed_flexibility_working(sys, results, "elec_demand", "elec_demand_elec_near_consumes")


if __name__ == "__main__":
    run_test()

### ANALYTICAL RESULTS ###

# Since the demand is fixed, the optimizer must find the cheapest way to produce the required
# amount of electricity at each timestep. The problem is set up such that, to produce the required
# 120 units of elec_near, electricity must be drawn from the two cheapest sources. Thus, of the
# three sources, one will be producing at maximum capacity, one will be producing at partial
# capacity, and one will not be producing. This order should be determined by their relative
# costs of production at each timestep.

# For elec_plant_near:
#     Cost to produce elec_near = near_plant_om = [4, 4, 8, 12, 8, 12]
# For elec_plant_far:
#     Cost to produce elec_near = far_plant_om / (far transfer ratio)
#                               = [6, 9, 3, 3, 9, 6] / 0.75
# For elec_plant_farther:
#     Cost to produce elec_near = farther_plant_om / (farther transfer ratio)
#                                 [6, 4, 6, 4, 2, 2] / 0.5

# Thus the cost to satisfy one unit of elec_near demand is as follows:
#         | t0  | t1  | t2  | t3  | t4  | t5  |
# ------- |-----|-----|-----|-----|-----|-----|
#    near | $4  | $4  | $8  | $12 | $8  | $12 |
#     far | $8  | $12 | $4  | $4  | $12 | $8  |
# farther | $12 | $8  | $12 | $8  | $4  | $4  |

# For each timestep, the plant that produces elec_near at a relative cost of $4 should be
# dispatched first, and should show a production rate of 100 in the results. This production should
# be supplemented by the plant with a relative elec_near cost of $8, which should be observed to
# produce electricity at partial capacity (less than 100). The plant with a relative cost of $12 at
# each timestep should have a production of 0 in the results.
