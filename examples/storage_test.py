# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import numpy as np

import dove.core as dc

if __name__ == "__main__":
    ############################
    ### System Resources
    ############################
    elec = dc.Resource("electricity")
    steam = dc.Resource("steam")

    ############################
    ### Time-Series Profiles
    ############################
    linear_price = np.arange(0.1, 2.2, 0.1)
    spike_price = np.zeros(len(linear_price), dtype=np.float64)
    spike_price.put((0, 11, 20), 10)

    ##########################
    ### Component Definitions
    ##########################

    # A Source doesn't consume any resources and produces a singular resource.
    # Notice how `flexibility` is set on this component. A fixed flexibility
    # indicates that the component will produce `steam` at max_capacity for each time step.
    # This is also the reason why `profile` is not set for this component.
    # There are also no cashflows associated with producing steam from the "steamer."
    steamer = dc.Source(
        name="steamer",
        produces=steam,
        max_capacity_profile=np.full(len(linear_price), 100),
        flexibility="fixed",
    )

    # A Storage component doesn't specify a `consumes` and `produces` but defines
    # a `resource` that its capacity is defined in terms of. A Storage can only store
    # a singular resource and dispatch it at a later point in time when advantageous.
    steam_storage = dc.Storage(
        name="steam_storage",
        resource=steam,
        max_capacity_profile=np.full(len(linear_price), 100),
        rte=0.9,
    )

    # A Converter can consume and produce multiple resources. If a Converter produces
    # resources that are different from what it consumes, `transfer_terms` must be defined
    # so the resource knows how to convert resources to contribute to the system.
    gen = dc.Converter(
        name="generator",
        consumes=[steam],
        produces=[elec],
        max_capacity_profile=np.full(len(linear_price), 90),
        capacity_resource=steam,
        transfer_fn=dc.RatioTransfer(input_resources={steam: 1.0}, output_resources={elec: 0.5}),
    )

    # A Sink can only consume one resource. These components typically represent
    # some kind of "grid" or "market" that resources in the system are distributed to.
    # Revenue cash flows are defined to motivate the optimizer to dispatch resources
    # to its respective market.
    market_linear = dc.Sink(
        name="market_linear",
        consumes=elec,
        max_capacity_profile=np.full(len(linear_price), 2),
        cashflows=[dc.Revenue("esales", price_profile=linear_price)],  # Time Varying Revenue
    )

    market_spike = dc.Sink(
        name="market_spike",
        consumes=elec,
        max_capacity_profile=np.full(len(linear_price), 40),
        cashflows=[dc.Revenue("esales", price_profile=spike_price)],  # Time Varying Revenue
    )

    steam_offload = dc.Sink(
        name="steam_offload",
        consumes=steam,
        max_capacity_profile=np.full(len(linear_price), 100),
        cashflows=[dc.Revenue("steam_offload", alpha=0.01)],  # Constant Revenue
    )

    ############################
    ### System Definition
    ############################
    components = [steamer, steam_storage, gen, market_linear, market_spike, steam_offload]
    resources = [elec, steam]
    time_index = np.arange(0, len(linear_price))
    sys = dc.System(components, resources, time_index)
    results = sys.solve()

    print(results)
