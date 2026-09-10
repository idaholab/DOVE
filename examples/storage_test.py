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
    # indicates that the component will produce `steam` at installed_capacity for each time step.
    # There are also no cashflows associated with producing steam from the "steamer."
    steamer = dc.Source(
        name="steamer",
        produces=steam,
        installed_capacity=100,
        flexibility="fixed",
    )

    # A Storage component doesn't specify a `consumes` and `produces` but defines
    # a `resource` that its capacity is defined in terms of. A Storage can only store
    # a singular resource and dispatch it at a later point in time when advantageous.
    steam_storage = dc.Storage(
        name="steam_storage",
        resource=steam,
        installed_capacity=100,
        rte=0.9,
    )

    # A Converter can consume and produce multiple resources. The mathematical relationship
    # governing this conversion is specified in the `transfer_fn`.
    gen = dc.Converter(
        name="generator",
        consumes=[steam],
        produces=[elec],
        installed_capacity=90,
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
        installed_capacity=2,
        cashflows=[dc.Revenue("esales", price_profile=linear_price)],  # Time Varying Revenue
    )

    market_spike = dc.Sink(
        name="market_spike",
        consumes=elec,
        installed_capacity=40,
        cashflows=[dc.Revenue("esales", price_profile=spike_price)],  # Time Varying Revenue
    )

    steam_offload = dc.Sink(
        name="steam_offload",
        consumes=steam,
        installed_capacity=100,
        cashflows=[dc.Revenue("steam_offload", alpha=0.01)],  # Constant Revenue
    )

    ############################
    ### System Definition
    ############################
    components = [steamer, steam_storage, gen, market_linear, market_spike, steam_offload]
    resources = [elec, steam]
    dispatch_window = np.arange(0, len(linear_price))
    sys = dc.System(components, resources, dispatch_window)
    results = sys.solve()

    print(results)
