
"""
"""
import numpy as np
import matplotlib.pyplot as plt
import pyomo.environ as pyo
import pandas as pd
from .components import Resource, TransferTerm, Revenue, Cost, Source, Sink, Converter, Storage
from .system import System


if __name__ == '__main__':
    elec = Resource("electricity")
    steam = Resource("steam")

    steamer = Source(
        name="steamer",
        produces=steam,
        capacity=100,
        dispatch_flexibility="fixed"
    )

    steam_storage = Storage(
        name="steam_storage",
        resource=steam,
        capacity=100,
        rte=0.9,
    )

    gen = Converter(
        name="generator",
        capacity_resource=steam,
        capacity=90,
        consumes=[steam],
        produces=elec,
        transfer_terms=[
            TransferTerm(1, {steam: 1}),
            TransferTerm(0.5, {elec: 1})
        ]
    )

    linear_price = np.arange(0.1, 2.2, 0.1).tolist() * 2
    market_linear = Sink(
        name="market_linear",
        consumes=elec,
        capacity=2,
        cashflows=[Revenue("esales", linear_price)],
    )

    spike_price = np.zeros(len(linear_price))
    spike_price.put((0, 11, 20, 28, 29, 38), 10)
    market_spike = Sink(
        name="market_spike",
        consumes=elec,
        capacity=40,
        cashflows=[Revenue("esales", spike_price.tolist())],
    )

    steam_offload = Sink(
        name="steam_offload",
        consumes=steam,
        capacity=100,
        cashflows=[Revenue("steam_offload", 0.01)],
    )

    components = [steamer, steam_storage, gen, market_linear, market_spike, steam_offload]
    resources = [elec, steam]
    sys = System(components, resources, np.arange(0, len(linear_price)).tolist())
    model = sys.solve()

    time_index = sys.time_index
    comp_names = list(sys.comp_map.keys())

    # Extract dispatch into a DataFrame
    data = {
        comp: [pyo.value(model.dispatch[comp, t]) for t in time_index]
        for comp in comp_names
    }
    df = pd.DataFrame(data, index=time_index)
    print(df)

    # Plot the dispatch schedules
    plt.figure()
    for comp in comp_names:
        plt.plot(time_index, df[comp], label=comp)
    plt.xlabel("Time")
    plt.ylabel("Dispatch")
    plt.title("Component Dispatch over Time")
    plt.legend()
    plt.show()




