# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Demonstrates a minimal example of using DOVE. See images/energy_flow_diagram_minimal.png
for a diagram of resource flows in the system set up here.
"""

import dove.core as dc

steam = dc.Resource(name="steam")
elec = dc.Resource(name="electricity")

nuclear = dc.Source(name="nuclear", produces=steam, installed_capacity=3)
gen = dc.Converter(
    name="generator",
    consumes=[steam],
    produces=[elec],
    capacity_resource=elec,
    installed_capacity=3,
    transfer_fn=dc.RatioTransfer(input_resources={steam: 1.0}, output_resources={elec: 1.0}),
)
wind = dc.Source(name="wind", produces=elec, installed_capacity=2, capacity_factor=[0.5, 1.0])
battery = dc.Storage(name="battery", resource=elec, installed_capacity=1, rte=0.9)
grid = dc.Sink(
    name="grid",
    consumes=elec,
    demand_profile=[3, 6],
    cashflows=[dc.Revenue(name="elec_sales", alpha=1.0)],
)

sys = dc.System(
    components=[nuclear, gen, wind, battery, grid], resources=[steam, elec], dispatch_window=[0, 1]
)
results = sys.solve("price_taker")
print(results)
with open("simple_demo.csv", "w") as f:
    f.write(results.to_csv())
