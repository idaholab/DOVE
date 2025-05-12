# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
"""
import numpy as np

from dove import Converter, Resource, Revenue, Sink, Source, System, Storage, TransferTerm

if __name__ == '__main__':

    ############################
    ### System Resources
    ############################
    elec = Resource("electricity")
    steam = Resource("steam")

    ############################
    ### Time-Series Profiles
    ############################
    linear_price = np.arange(0.1, 2.2, 0.1)
    spike_price = np.zeros(len(linear_price))
    spike_price.put((0, 11, 20), 10)

    ##########################
    ### Component Definitions
    ##########################

    # A Source doesn't consume any resources and produces a singular resource.
    # Notice how `flexibility` is set on this component. A fixed flexibility
    # indicates that the component will produce `steam` at max_capacity for each time step.
    # This is also the reason why `profile` is not set for this component.
    # There are also no cashflows associated with producing steam from the "steamer."
    steamer = Source(
        name="steamer",
        produces=steam,
        max_capacity=100,
        flexibility="fixed"
    )

    # A Storage component doesn't specify a `consumes` and `produces` but defines
    # a `resource` that its capacity is defined in terms of. A Storage can only store
    # a singluar resource and dispatch it at a later point in time when advantageous.
    steam_storage = Storage(
        name="steam_storage",
        resource=steam,
        max_capacity=100,
        rte=0.9,
    )

    # A Converter can consume and produce multiple resources. If a Converter produces
    # resources that are different from what it consumes, `transfer_terms` must be defined
    # so the resource knows how to convert resources to contribute to the system.
    gen = Converter(
        name="generator",
        consumes=[steam],
        produces=[elec],
        max_capacity=90,
        capacity_resource=steam,
        transfer_terms=[
            TransferTerm(1, {steam: 1}),
            TransferTerm(0.5, {elec: 1})
        ]
    )

    # A Sink can only consume one resource. These components typically represent
    # some kind of "grid" or "market" that resources in the system are distributed to.
    # Revenue cash flows are defined to motivate the optimizer to dispatch resources
    # to its respective market.
    market_linear = Sink(
        name="market_linear",
        consumes=elec,
        max_capacity=2,
        cashflows=[Revenue("esales", price_profile=linear_price)]
    )

    market_spike = Sink(
        name="market_spike",
        consumes=elec,
        max_capacity=40,
        cashflows=[Revenue("esales", price_profile=spike_price)],
    )

    steam_offload = Sink(
        name="steam_offload",
        consumes=steam,
        max_capacity=100,
        cashflows=[Revenue("steam_offload", alpha=0.01)],
    )

    ############################
    ### System Definition
    ############################
    components = [steamer, steam_storage, gen, market_linear, market_spike, steam_offload]
    resources = [elec, steam]
    time_index = np.arange(0, len(linear_price))
    sys = System(components, resources, time_index)
    results = sys.solve()

    print(results)




