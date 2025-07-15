#!/usr/bin/env python
# Copyright 2024, Battelle Energy Alliance, LLC
""" """

import numpy as np

import dove.core as dc

if __name__ == "__main__":
    # Time series data:
    prices = np.array([0, 0, 0, 2, 1])

    # Resources
    resrc = dc.Resource("resource")

    # Cashflows
    sales = dc.Revenue(name="sales", price_profile=prices)

    # Components
    src = dc.Source(name="source", installed_capacity=2, produces=resrc, flexibility="fixed")

    storg = dc.Storage(
        name="storage",
        resource=resrc,
        installed_capacity=4,
        max_charge_rate=0.25,
        max_discharge_rate=0.5,
    )

    sink = dc.Sink(
        name="sink", consumes=resrc, demand_profile=[10, 10, 10, 10, 10], cashflows=[sales]
    )

    sys = dc.System([src, storg, sink], [resrc], [0, 1, 2, 3, 4])
    results = sys.solve()
    print(results)
