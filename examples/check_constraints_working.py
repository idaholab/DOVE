# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Defines some functions that can be used to check whether constraints are working properly
"""

import numpy as np


def max_capacity_profile_working(sys, results, comp_name, activity_col):
    comp = sys.comp_map[comp_name]
    activity_profile = results.loc[:, activity_col].values

    if (abs(activity_profile) < comp.max_capacity_profile + 1e-6).all():
        print(f"✅ Max capacity profile constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Max capacity profile constraints violated for {comp_name}!")

    new_max_capacity_profile = np.multiply(comp.max_capacity_profile, 2)
    confirm_economic_motivation(
        sys, results, comp_name, "max_capacity_profile", new_max_capacity_profile
    )
    print()


def min_capacity_profile_working(sys, results, comp_name, activity_col):
    comp = sys.comp_map[comp_name]
    activity_profile = results.loc[:, activity_col].values

    if (abs(activity_profile) > comp.min_capacity_profile - 1e-6).all():
        print(f"✅ Min capacity profile constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Min capacity profile constraint violated for {comp_name}!")

    new_min_capacity_profile = np.full(len(sys.time_index), 0)
    confirm_economic_motivation(
        sys, results, comp_name, "min_capacity_profile", new_min_capacity_profile
    )
    print()


def fixed_flexibility_working(sys, comp_name):
    comp = sys.comp_map[comp_name]

    if np.all(comp.min_capacity_profile == comp.max_capacity_profile):
        print(f"✅ Fixed flexibility constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Fixed flexibility constraint violated for {comp_name}!")


def ramp_limit_working(sys, results, comp_name, column_name):
    comp = sys.comp_map[comp_name]
    activity_profile = results.loc[:, column_name].values

    ramp_rates = np.abs(np.diff(activity_profile))
    if np.all(ramp_rates <= (comp.ramp_limit * np.max(comp.max_capacity_profile)) + 1e-6):
        print(f"✅ Ramp rate limit constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Ramp rate limit constraint violated for {comp_name}!")

    new_ramp_limit = 1.0
    confirm_economic_motivation(sys, results, comp_name, "ramp_limit", new_ramp_limit)
    print()


def ramp_freq_working(sys, results, comp_name, column_name):
    comp = sys.comp_map[comp_name]
    activity_profile = results.loc[:, column_name].values
    ramp_rates = np.abs(np.diff(activity_profile))

    # Count ramp events
    # Define a significant ramp as >5% of max capacity
    ramp_threshold = 0.05 * np.max(comp.max_capacity_profile)
    ramp_events = ramp_rates > ramp_threshold
    ramps_per_window = []
    for i in range(len(ramp_events) - comp.ramp_freq + 1):
        window = ramp_events[i : i + comp.ramp_freq]
        ramps_per_window.append(np.sum(window))

    if np.max(ramps_per_window) <= 1:
        print(f"✅ Ramp frequency constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Ramp frequency constraint violated for {comp_name}!")

    new_ramp_freq = 0.0
    confirm_economic_motivation(sys, results, comp_name, "ramp_freq", new_ramp_freq)
    print()


def max_charge_rate_working(sys, results, comp_name):
    comp = sys.comp_map[comp_name]
    charge = results.loc[:, f"{comp_name}_charge"].values

    if np.max(charge) < comp.max_charge_rate * np.max(comp.max_capacity_profile) + 1e-6:
        print(f"✅ Max charge constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Max charge constraint violated for {comp_name}!")

    new_max_charge_rate = 1.0
    confirm_economic_motivation(sys, results, comp_name, "max_charge_rate", new_max_charge_rate)
    print()


def max_discharge_rate_working(sys, results, comp_name):
    comp = sys.comp_map[comp_name]
    discharge = results.loc[:, f"{comp_name}_discharge"].values

    if np.max(discharge) < comp.max_discharge_rate * np.max(comp.max_capacity_profile) + 1e-6:
        print(f"✅ Max discharge constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Max discharge constraint violated for {comp_name}!")

    new_max_discharge_rate = 1.0
    confirm_economic_motivation(
        sys, results, comp_name, "max_discharge_rate", new_max_discharge_rate
    )
    print()


def rte_working(sys, results, comp_name):
    # Note: implicitly checks storage balance as well
    comp = sys.comp_map[comp_name]
    soc = results.loc[:, f"{comp_name}_SOC"].values
    charge = results.loc[:, f"{comp_name}_charge"].values
    discharge = results.loc[:, f"{comp_name}_discharge"].values

    soc_diff = np.concatenate(
        (np.array([soc[0] - comp.initial_stored * np.max(comp.max_capacity_profile)]), np.diff(soc))
    )
    if np.all(abs(soc_diff - charge * comp.rte**0.5 + discharge / comp.rte**0.5) < 1e-6):
        print(f"✅ RTE constraint working correctly for {comp_name}!")
    else:
        print(f"❌ RTE constraint violated for {comp_name}!")

    new_rte = 1.0
    confirm_economic_motivation(sys, results, comp_name, "rte", new_rte)
    print()


def periodic_storage_working(sys, results, comp_name):
    comp = sys.comp_map[comp_name]
    soc = results.loc[:, f"{comp_name}_SOC"].values

    if abs(soc[-1] - (comp.initial_stored * np.max(comp.max_capacity_profile))) < 1e-6:
        print(f"✅ Periodic storage constraint working correctly for {comp_name}!")
    else:
        print(f"❌ Periodic storage constraint violated for {comp_name}!")

    new_periodic_level = False
    confirm_economic_motivation(sys, results, comp_name, "periodic_level", new_periodic_level)
    print()


def confirm_economic_motivation(sys, orig_results, comp_name, attribute, new_value):
    comp = sys.comp_map[comp_name]
    orig_value = getattr(comp, attribute)
    setattr(comp, attribute, new_value)

    new_results = sys.solve("price_taker")

    if orig_results.loc[0, "objective"] < new_results.loc[0, "objective"]:
        print(
            f"Objective increased when {comp_name} {attribute} was set to {new_value}, "
            f"implying that there is economic motivation to violate {attribute} constraint"
        )
    else:
        print(
            f"Objective did not increase when {comp_name} {attribute} was set to {new_value}, "
            f"implying that there is a lack of economic motivation to violate {attribute} constraint"
        )

    setattr(comp, attribute, orig_value)
