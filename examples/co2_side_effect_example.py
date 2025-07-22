# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Demonstrates a problem where components emit co2, which is tracked and limited to a certain
quantity through the whole dispatch period.
"""

import dove.core as dc

# Resources
elec = dc.Resource(name="electricity")
co2 = dc.Resource(name="carbon_dioxide")
dgen_production = dc.Resource(name="dgen_production")

# Electricity-producing components
# Note that all values are fictional
# There are two possible ways to track how much CO2 is produced by the system
# Option 1: define a custom component with multiple production resources
ngcc = dc.Component(
    name="ngcc",
    produces=[elec, co2],
    max_capacity_profile=[3.0, 3.0, 3.0],
    capacity_resource=elec,
    transfer_fn=dc.RatioTransfer(input_resources={}, output_resources={elec: 1.0, co2: 2.0}),
    cashflows=[dc.Cost(name="OM_and_fuel", alpha=2.0)],
)

# Option 2: use a converter to transfer production quantity to electricity and co2
diesel_gen = dc.Source(
    name="diesel_gen",
    produces=dgen_production,
    max_capacity_profile=[2.0, 2.0, 2.0],
    cashflows=[dc.Cost(name="OM_and_fuel", alpha=3.0)],
)
dgen_prod_converter = dc.Converter(
    name="dgen_prod_converter",
    max_capacity_profile=[2.0, 2.0, 2.0],
    consumes=[dgen_production],
    produces=[elec, co2],
    capacity_resource=dgen_production,
    transfer_fn=dc.RatioTransfer(
        input_resources={dgen_production: 1.0}, output_resources={elec: 1.0, co2: 4.0}
    ),
)

nuclear = dc.Source(
    name="nuclear",
    max_capacity_profile=[4.0, 4.0, 4.0],
    produces=elec,
    cashflows=[dc.Cost(name="OM_and_fuel", alpha=2.0)],
)

# Electricity-consuming components
grid = dc.Sink(
    name="grid",
    consumes=elec,
    max_capacity_profile=[9.0, 6.0, 8.0],
    cashflows=[dc.Revenue(name="elec_sales", price_profile=[4.0, 4.0, 3.0])],
)

# Components for enforcing a maximum co2 production
# Since resources must be conserved, this storage effectively restricts the amount of co2 emitted
# by the system by enforcing that the accumulated amount never exceeds the given capacity
co2_accumulation = dc.Storage(
    name="co2_accumulation",
    resource=co2,
    max_capacity_profile=[20.0, 20.0, 20.0],
    periodic_level=False,
)

# System
sys = dc.System(
    components=[ngcc, diesel_gen, dgen_prod_converter, nuclear, grid, co2_accumulation],
    resources=[elec, co2, dgen_production],
    time_index=[0, 1, 2],
)

results = sys.solve("price_taker")
print(results)
with open("co2_side_effect.csv", "w") as f:
    f.write(results.to_csv())
