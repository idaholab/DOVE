# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
"""
import numpy as np

from dove.core import Converter, Resource, Revenue, Sink, Source, Storage, TransferTerm
from dove.core.system import System

if __name__ == '__main__':

    ### System Resources
    elec = Resource("electricity")
    steam = Resource("steam")

    ### Time-Series Profiles
    linear_price = np.arange(0.1, 2.2, 0.1).tolist() * 2
    spike_price = np.zeros(len(linear_price))
    spike_price.put((0, 11, 20, 28, 29, 38), 10)


    ### Component Definitions
    steamer = Source(name="steamer", produces=steam, max_capacity=100, flexibility="fixed")
    steam_storage = Storage(name="steam_storage", resource=steam, max_capacity=100, rte=0.9)

    gen = Converter(
        name="generator",
        capacity_resource=steam,
        max_capacity=90,
        consumes=[steam],
        produces=[elec],
        transfer_terms=[
            TransferTerm(1, {steam: 1}),
            TransferTerm(0.5, {elec: 1})
        ]
    )

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
        cashflows=[Revenue("esales", price_profile=spike_price.tolist())],
    )

    steam_offload = Sink(
        name="steam_offload",
        consumes=steam,
        max_capacity=100,
        cashflows=[Revenue("steam_offload", alpha=0.01)],
    )

    ### System Definition
    components = [steamer, steam_storage, gen, market_linear, market_spike, steam_offload]
    resources = [elec, steam]
    time_index = np.arange(0, len(linear_price)).tolist()
    sys = System(components, resources, time_index)
    results = sys.solve()

    print(results)




