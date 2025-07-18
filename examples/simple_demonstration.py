# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Demonstrates a minimal example of using DOVE. See images/energy_flow_diagram_minimal.png
for a diagram of resource flows in the system set up here.
"""

import dove.core as dc

steam = dc.Resource(name="steam")
elec = dc.Resource(name="electricity")

nuclear = dc.Source(name="nuclear", produces=steam, max_capacity_profile=[3, 3])
gen = dc.Converter(
    name="generator",
    consumes=[steam],
    produces=[elec],
    capacity_resource=elec,
    max_capacity_profile=[3, 3],
    transfer_fn=dc.RatioTransfer(input_res=steam, output_res=elec, ratio=1.0),
)
wind = dc.Source(name="wind", produces=elec, max_capacity_profile=[1, 2])
battery = dc.Storage(name="battery", resource=elec, max_capacity_profile=[1, 1], rte=0.9)
grid = dc.Sink(
    name="grid",
    consumes=elec,
    max_capacity_profile=[3, 6],
    cashflows=[dc.Revenue(name="elec_sales", alpha=1.0)],
)

sys = dc.System(
    components=[nuclear, gen, wind, battery, grid], resources=[steam, elec], time_index=[0, 1]
)
results = sys.solve("price_taker")
print(results)
with open("simple_demo.csv", "w") as f:
    f.write(results.to_csv())
