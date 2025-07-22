# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
This example shows how DOVE can handle multiple commodities with their own respective markets.
"""

import numpy as np

import dove.core as dc


def run_test():
    # Resources
    potatoes = dc.Resource("potatoes")
    potato_chips = dc.Resource("potato_chips")

    # Components
    potato_farms = dc.Source(
        "potato_farms",
        produces=potatoes,
        max_capacity_profile=np.full(4, 100),
        flexibility="fixed",
    )

    potato_chip_factory = dc.Converter(
        name="potato_chip_factory",
        max_capacity_profile=np.full(4, 80),
        consumes=[potatoes],
        produces=[potato_chips],
        capacity_resource=potatoes,
        transfer_fn=dc.RatioTransfer(
            input_resources={potatoes: 1.0}, output_resources={potato_chips: 1.0}
        ),
    )

    # Note the two sinks for the dispatcher to choose from
    potato_market = dc.Sink(
        name="potato_market",
        consumes=potatoes,
        max_capacity_profile=np.full(4, 100),
        cashflows=[dc.Revenue("potato_revenue", price_profile=[1, 2, 3, 4])],
    )

    potato_chip_market = dc.Sink(
        name="potato_chip_market",
        consumes=potato_chips,
        max_capacity_profile=np.full(4, 100),
        cashflows=[dc.Revenue("potato_chip_revenue", alpha=3)],
    )

    # System
    sys = dc.System(
        components=[potato_farms, potato_chip_factory, potato_market, potato_chip_market],
        resources=[potatoes, potato_chips],
        time_index=np.arange(0, 4),
    )

    # Solution
    results = sys.solve("price_taker")
    print(results)
    with open("potato.csv", "w") as f:
        f.write(results.to_csv())


if __name__ == "__main__":
    run_test()

### ANALYTICAL SOLUTION ###
# Since the flexibility of the source is fixed, the only thing the dispatcher can decide is whether
# to sell on the potato_market or to convert the potatoes to potato chips and sell on the
# potato_chip_market. The converter is 1:1, so it's just a matter of which Revenue offers a higher
# price at each timestep.

#                   | t0 | t1 | t2 | t3 |
#                   |----|----|----|----|
#      potato price | $1 | $2 | $3 | $4 |
# potato chip price | $3 | $3 | $3 | $3 |

# Based on these prices, we can expect to see the potato_chip_market fully dispatched for the first
# two timesteps and the potato_market fully dispatched for the final timestep.
