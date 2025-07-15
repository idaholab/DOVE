# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import numpy as np

import dove.core as dc

if __name__ == "__main__":
    elec = dc.Resource("electricity")

    wind_cap_fac_ts = np.array(
        [
            7.55000000e-10,
            6.27905200e-02,
            1.25333234e-01,
            1.87381315e-01,
            2.48689888e-01,
            3.09016995e-01,
            3.68124553e-01,
            4.25779292e-01,
            4.81753675e-01,
            5.35826796e-01,
            5.87785253e-01,
            6.37423990e-01,
            6.84547106e-01,
            7.28968628e-01,
            7.70513243e-01,
            8.09016995e-01,
            8.44327926e-01,
            8.76306680e-01,
            9.04827053e-01,
            9.29776486e-01,
            9.51056517e-01,
        ]
    )

    wind = dc.Source(
        name="wind",
        produces=elec,
        installed_capacity=10,
        capacity_factor=wind_cap_fac_ts,
    )

    npp = dc.Source(
        name="npp",
        produces=elec,
        installed_capacity=20,
        cashflows=[dc.Cost("var_OM", alpha=3.5e3)],
    )

    grid = dc.Sink(
        name="grid",
        consumes=elec,
        demand_profile=[35] * len(wind_cap_fac_ts),
        flexibility="fixed",
        cashflows=[dc.Revenue("e_sales", alpha=50e3)],
    )

    importelec = dc.Source(
        name="import",
        produces=elec,
        installed_capacity=100,
        cashflows=[dc.Cost("import", alpha=1e6)],
    )

    exportelec = dc.Sink(
        name="export",
        consumes=elec,
        demand_profile=[100] * len(wind_cap_fac_ts),
        cashflows=[dc.Cost("export", alpha=1e6)],
    )

    sys = dc.System(
        components=[wind, npp, grid, importelec, exportelec],
        resources=[elec],
        dispatch_window=np.arange(0, len(wind_cap_fac_ts)),
    )
    results = sys.solve()
    print(results)
