# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""This example demonstrates how to force the activity of Components to exceed a minimum value."""

import dove.core as dc

res = dc.Resource(name="res")
production = dc.Source(
    name="production",
    produces=res,
    installed_capacity=6,
    capacity_factor=[0.75, 1.0, 0.75],
    min_capacity_factor=[0.5, 0.5, 0.5],
    cashflows=[dc.Cost(name="OM_costs", price_profile=[2, 2, 2])],
)

market_1 = dc.Sink(
    name="market_1",
    consumes=res,
    demand_profile=[3, 3, 4],
    min_demand_profile=[1, 2, 2],
    cashflows=[dc.Revenue(name="price_spike", price_profile=[1, 1, 8])],
)

market_2 = dc.Sink(
    name="market_2",
    consumes=res,
    installed_capacity=2,
    min_capacity_factor=[0.25, 0.5, 0.5],
    cashflows=[dc.Revenue(name="sales", price_profile=[1, 3, 3])],
)

sys = dc.System(
    components=[production, market_1, market_2], resources=[res], dispatch_window=[0, 1, 2]
)

results = sys.solve("price_taker")
print(results)
