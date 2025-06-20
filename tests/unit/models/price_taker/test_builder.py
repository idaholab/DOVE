# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from itertools import product

import pandas as pd
import pyomo.environ as pyo
import pytest

import dove.core as dc
from dove.models import BUILDER_REGISTRY


@pytest.fixture()
def create_example_system():
    """
    This establishes a simple system on which we can test the builder.
    It features multiple resources, multiple storage and non-storage components, and multiple timesteps.
    """

    ### Set up resources

    steam = dc.Resource("steam")
    elec = dc.Resource("electricity")

    resources = [steam, elec]

    ### Set up components

    # Non-storage
    steam_source = dc.Source(
        name="steam_source",
        produces=steam,
        max_capacity_profile=[2.0, 2.0, 2.0],
    )

    steam_to_elec_converter = dc.Converter(
        name="steam_to_elec_converter",
        max_capacity_profile=[1.0, 1.0, 1.0],
        consumes=[steam],
        produces=[elec],
        capacity_resource=steam,
        transfer_fn=dc.RatioTransfer(input_res=steam, output_res=elec, ratio=0.5),
    )

    elec_sink = dc.Sink(
        name="elec_sink",
        consumes=elec,
        max_capacity_profile=[1.0, 1.0, 1.0],
        min_capacity_profile=[0.5, 0.5, 0.5],
    )

    # Storage
    steam_storage = dc.Storage(
        name="steam_storage", resource=steam, max_capacity_profile=[1.0, 1.0, 1.0]
    )

    elec_storage = dc.Storage(
        name="elec_storage",
        resource=elec,
        max_charge_rate=0.5,
        max_discharge_rate=0.25,
        max_capacity_profile=[2.0, 2.0, 2.0],
    )

    components = [steam_source, steam_to_elec_converter, elec_sink, steam_storage, elec_storage]

    ### Set up times
    time_index = [0, 1, 2]

    ### Create and return system
    sys = dc.System(components, resources, time_index)
    return sys


@pytest.fixture()
def builder_setup(create_example_system):
    price_taker_builder_cls = BUILDER_REGISTRY["price_taker"]
    price_taker_builder = price_taker_builder_cls(create_example_system)
    price_taker_builder.model = pyo.ConcreteModel()
    price_taker_builder.model.system = price_taker_builder.system

    return price_taker_builder


def test_add_sets(builder_setup):
    # Call method under test
    builder_setup._add_sets()

    # Find the actual pyo.Set objects and extract data as tuples of strings

    m = builder_setup.model

    actual_non_storage = m.NON_STORAGE.data()
    actual_storage = m.STORAGE.data()
    actual_r = m.R.data()
    actual_t = m.T.data()

    # Find the expected values for the sets as lists of strings

    sys = builder_setup.system

    expected_non_storage = sys.non_storage_comp_names
    expected_storage = sys.storage_comp_names
    expected_r = [r.name for r in sys.resources]
    expected_t = sys.time_index

    # Convert both actual (tuple) and expected (list) values to the same types and check their values

    assert set(actual_non_storage) == set(expected_non_storage)
    assert set(actual_storage) == set(expected_storage)
    assert set(actual_r) == set(expected_r)
    assert list(actual_t) == expected_t  # We do care about the order for this one


def test_add_variables(builder_setup):
    # Add sets to builder so the variables can use them
    builder_setup._add_sets()

    # Call method under test
    builder_setup._add_variables()

    # Find the actual pyo.Var objects and extract data into dicts, then get the set of keys
    # We care about the keys because these are the bins for the var to later populate with values

    m = builder_setup.model

    actual_flow_keys = set(m.flow.get_values().keys())
    actual_soc_keys = set(m.soc.get_values().keys())
    actual_charge_keys = set(m.charge.get_values().keys())
    actual_discharge_keys = set(m.discharge.get_values().keys())

    # Build combinations for keys in expected content of vars

    sys = builder_setup.system
    res_names = [r.name for r in sys.resources]

    expected_flow_keys = set(product(sys.non_storage_comp_names, res_names, sys.time_index))
    expected_storage_keys = set(product(sys.storage_comp_names, sys.time_index))

    # Check that sets of keys are as expected
    assert actual_flow_keys == expected_flow_keys
    assert actual_soc_keys == expected_storage_keys
    assert actual_charge_keys == expected_storage_keys
    assert actual_discharge_keys == expected_storage_keys


@pytest.fixture()
def add_constraints_setup(builder_setup):
    # Add sets and variables to builder so the constraints can use them
    builder_setup._add_sets()
    builder_setup._add_variables()

    # Call method under test
    builder_setup._add_constraints()
    return builder_setup


@pytest.fixture()
def check_constraint():
    def _check_constraint(
        model: pyo.ConcreteModel, constr_name: str, is_equality_constr: bool, expected_result: dict
    ) -> None:
        """
        Ensure constraint is correct by checking that it exists, that the keys are correct,
        that it is is of the type (equality/inequality) expected, and that it is satisfied when expected.

        Parameters
        ----------
        model: pyo.ConcreteModel
            The Pyomo model on which the constraints are being tested.
        constr_name: str
            The expected name of the constraint on the model.
        is_equality_constr: bool
            Whether this constraint is expected to be an equality constraint (created with ==).
        expected_result: dict
            A dict with keys that are tuples that mirror the expected keys of the constraint (or bins for the
            constraint to populate) and values that are bools with the expected feasibility of the constraint.
        """
        actual_constr = getattr(model, constr_name, None)

        assert actual_constr is not None
        assert set(actual_constr.keys()) == set(expected_result.keys())

        for (
            case,  # Cases are tuples (e.g., ("steam_source", 0))
            value,  # Values are bools (for whether the constraint should be feasible)
        ) in expected_result.items():
            specific_constr = actual_constr[case]

            assert specific_constr.equality == is_equality_constr
            assert specific_constr.has_lb() or specific_constr.has_ub()

            satisfies_lb = (
                (specific_constr.body() >= specific_constr.lb) if specific_constr.has_lb() else True
            )
            satisfies_ub = (
                (specific_constr.body() <= specific_constr.ub) if specific_constr.has_ub() else True
            )
            assert (satisfies_lb and satisfies_ub) == value

    return _check_constraint


def test_add_constraints_adds_transfer_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model
    ### Transfer constraint

    # Set up required vars for input
    # Recall that for the converter, ratio_transfer ratio == 0.5
    m.flow.set_values(
        {
            ("steam_to_elec_converter", "steam",       0): 0.0,
            ("steam_to_elec_converter", "electricity", 0): 1.0,  # Out > 0.5 * In -> constr fails

            ("steam_to_elec_converter", "steam",       1): 2.0,
            ("steam_to_elec_converter", "electricity", 1): 1.0,  # Out == 0.5 * In -> constr satisfied

            ("steam_to_elec_converter", "steam",       2): 1.0,
            ("steam_to_elec_converter", "electricity", 2): 0.0,  # Out < 0.5 * In -> constr fails
        }
    )  # fmt: skip

    # Expected results
    expected_transfer_result = {
        ("steam_to_elec_converter", 0): False,
        ("steam_to_elec_converter", 1): True,
        ("steam_to_elec_converter", 2): False,
    }

    # Verify constraint
    check_constraint(m, "transfer", True, expected_transfer_result)


def test_add_constraints_adds_max_capacity_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    # Recall that:
    # steam_source.max_capacity_profile == [2.0, 2.0, 2.0]
    # steam_to_elec_converter.max_capacity_profile == [1.0, 1.0, 1.0]
    # elec_sink.max_capacity_profile == [1.0, 1.0, 1.0]
    m.flow.set_values(
        {
            ("steam_source", "steam", 0): 1.0,  # < max capacity -> constr satisfied
            ("steam_source", "steam", 1): 2.0,  # = max capacity -> constr satisfied
            ("steam_source", "steam", 2): 3.0,  # > max capacity -> constr fails
            ("steam_to_elec_converter", "steam", 0): 0.0,  # < max capacity -> constr satisfied
            ("steam_to_elec_converter", "steam", 1): 1.0,  # = max capacity -> constr satisfied
            ("steam_to_elec_converter", "steam", 2): 2.0,  # > max capacity -> constr fails
            ("elec_sink", "electricity", 0): 0.0,  # < max capacity -> constr satisfied
            ("elec_sink", "electricity", 1): 1.0,  # = max capacity -> constr satisfied
            ("elec_sink", "electricity", 2): 2.0,  # > max capacity -> constr fails
        }
    )

    # Expected results
    expected_cap_result = {
        ("steam_source", 0): True,
        ("steam_source", 1): True,
        ("steam_source", 2): False,
        ("steam_to_elec_converter", 0): True,
        ("steam_to_elec_converter", 1): True,
        ("steam_to_elec_converter", 2): False,
        ("elec_sink", 0): True,
        ("elec_sink", 1): True,
        ("elec_sink", 2): False,
    }

    # Verify constraint
    check_constraint(m, "max_capacity", False, expected_cap_result)


def test_add_constraints_adds_min_capacity_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    # Recall that elec_sink.min_capacity_profile == [0.5, 0.5, 0.5]; default is [0.0, 0.0, 0.0]
    m.flow.set_values(
        {
            ("steam_source", "steam", 0): 0.0,  # = min capacity -> constr satisfied
            ("steam_source", "steam", 1): 0.0,  # = min capacity -> constr satisfied
            ("steam_source", "steam", 2): 0.0,  # = min capacity -> constr satisfied
            ("steam_to_elec_converter", "steam", 0): 0.0,  # = min capacity -> constr satisfied
            ("steam_to_elec_converter", "steam", 1): 0.0,  # = min capacity -> constr satisfied
            ("steam_to_elec_converter", "steam", 2): 0.0,  # = min capacity -> constr satisfied
            ("elec_sink", "electricity", 0): 0.0,  # < min capacity -> constr fails
            ("elec_sink", "electricity", 1): 0.5,  # = min capacity -> constr satisfied
            ("elec_sink", "electricity", 2): 1.0,  # > min capacity -> constr satisfied
        }
    )

    # Expected results
    expected_min_cap_result = {
        ("steam_source", 0): True,
        ("steam_source", 1): True,
        ("steam_source", 2): True,
        ("steam_to_elec_converter", 0): True,
        ("steam_to_elec_converter", 1): True,
        ("steam_to_elec_converter", 2): True,
        ("elec_sink", 0): False,
        ("elec_sink", 1): True,
        ("elec_sink", 2): True,
    }

    # Verify constraint
    check_constraint(m, "min_capacity", False, expected_min_cap_result)


def test_add_constraints_adds_resource_balance_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    m.flow.set_values(
        {
            ("steam_source",            "steam",       0): 1.0,
            ("steam_to_elec_converter", "steam",       0): 1.0,
            ("steam_to_elec_converter", "electricity", 0): 1.0,
            ("elec_sink",               "electricity", 0): 1.0,
            ("steam_source",            "steam",       1): 2.0,
            ("steam_to_elec_converter", "steam",       1): 2.0,
            ("steam_to_elec_converter", "electricity", 1): 1.0,
            ("elec_sink",               "electricity", 1): 1.0,
            ("steam_source",            "steam",       2): 1.0,
            ("steam_to_elec_converter", "steam",       2): 1.0,
            ("steam_to_elec_converter", "electricity", 2): 1.0,
            ("elec_sink",               "electricity", 2): 1.0,
        }
    )  # fmt: skip

    m.charge.set_values(
        {
            ("steam_storage", 0): 0.0,
            ("steam_storage", 1): 1.0,
            ("steam_storage", 2): 2.0,
            ("elec_storage", 0): 0.0,
            ("elec_storage", 1): 1.0,
            ("elec_storage", 2): 2.0,
        }
    )

    m.discharge.set_values(
        {
            ("steam_storage", 0): 1.0,
            ("steam_storage", 1): 1.0,
            ("steam_storage", 2): 1.0,
            ("elec_storage", 0): 1.0,
            ("elec_storage", 1): 1.0,
            ("elec_storage", 2): 1.0,
        }
    )

    # Expected results
    expected_res_balance_result = {
        ("steam", 0): False,
        ("steam", 1): True,
        ("steam", 2): False,
        ("electricity", 0): False,
        ("electricity", 1): True,
        ("electricity", 2): False,
    }

    # Verify constraint
    check_constraint(m, "resource_balance", True, expected_res_balance_result)


def test_add_constraints_adds_storage_balance_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    # Recall that default rte == 1.0; default initial_stored == 0.0
    m.charge.set_values(
        {
            ("steam_storage", 0): 1.0,
            ("steam_storage", 1): 2.0,
            ("steam_storage", 2): 0.0,
            ("elec_storage", 0): 1.0,
            ("elec_storage", 1): 2.0,
            ("elec_storage", 2): 0.0,
        }
    )

    m.discharge.set_values(
        {
            ("steam_storage", 0): 0.0,
            ("steam_storage", 1): 1.0,
            ("steam_storage", 2): 0.0,
            ("elec_storage", 0): 0.0,
            ("elec_storage", 1): 1.0,
            ("elec_storage", 2): 0.0,
        }
    )

    m.soc.set_values(
        {
            ("steam_storage", 0): 0.0,
            ("steam_storage", 1): 1.0,
            ("steam_storage", 2): 2.0,
            ("elec_storage", 0): 0.0,
            ("elec_storage", 1): 1.0,
            ("elec_storage", 2): 2.0,
        }
    )

    # Expected results
    expected_storage_balance_result = {
        ("steam_storage", 0): False,
        ("steam_storage", 1): True,
        ("steam_storage", 2): False,
        ("elec_storage", 0): False,
        ("elec_storage", 1): True,
        ("elec_storage", 2): False,
    }

    # Verify constraint
    check_constraint(m, "storage_balance", True, expected_storage_balance_result)


def test_add_constraints_adds_charge_limit_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    # Recall that for steam storage, max_capacity_profile = [1, 1, 1], default max_charge_rate = 1
    # For elec storage, max_charge_rate = 0.5, max_capacity_profile = [2, 2, 2]
    m.charge.set_values(
        {
            ("steam_storage", 0): 0.0,  # < max_charge_rate * max capacity -> constr satisfied
            ("steam_storage", 1): 1.0,  # = max_charge_rate * max capacity -> constr satisfied
            ("steam_storage", 2): 2.0,  # > max_charge_rate * max capacity -> constr fails
            ("elec_storage", 0): 0.0,  # < max_charge_rate * max capacity -> constr satisfied
            ("elec_storage", 1): 1.0,  # = max_charge_rate * max capacity -> constr satisfied
            ("elec_storage", 2): 2.0,  # > max_charge_rate * max capacity -> constr fails
        }
    )

    # Expected results
    expected_charge_limit_result = {
        ("steam_storage", 0): True,
        ("steam_storage", 1): True,
        ("steam_storage", 2): False,
        ("elec_storage", 0): True,
        ("elec_storage", 1): True,
        ("elec_storage", 2): False,
    }

    # Verify constraint
    check_constraint(m, "charge_limit", False, expected_charge_limit_result)


def test_add_constraints_adds_discharge_limit_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    # Recall that for steam storage, max_capacity_profile = [1, 1, 1], default max_discharge_rate = 1
    # For elec storage, max_capacity_profile = [2, 2, 2], max_discharge_rate = 0.25
    m.discharge.set_values(
        {
            ("steam_storage", 0): 0.0,  # < max_discharge_rate * max capacity -> constr satisfied
            ("steam_storage", 1): 1.0,  # = max_discharge_rate * max capacity -> constr satisfied
            ("steam_storage", 2): 2.0,  # > max_discharge_rate * max capacity -> constr fails
            ("elec_storage", 0): 0.0,  # < max_discharge_rate * max capacity -> constr satisfied
            ("elec_storage", 1): 0.5,  # = max_discharge_rate * max capacity -> constr satisfied
            ("elec_storage", 2): 1.0,  # > max_discharge_rate * max capacity -> constr fails
        }
    )

    # Expected results
    expected_discharge_limit_result = {
        ("steam_storage", 0): True,
        ("steam_storage", 1): True,
        ("steam_storage", 2): False,
        ("elec_storage", 0): True,
        ("elec_storage", 1): True,
        ("elec_storage", 2): False,
    }

    # Verify constraint
    check_constraint(m, "discharge_limit", False, expected_discharge_limit_result)


def test_add_constraints_adds_soc_limit_constraint(add_constraints_setup, check_constraint):
    m = add_constraints_setup.model

    # Set up required vars for input
    # Recall that steam storage max_capacity_profile = [1, 1, 1]; elec storage max_capacity_profile = [2, 2, 2]
    m.soc.set_values(
        {
            ("steam_storage", 0): 0.0,  # < max capacity -> constr satisfied
            ("steam_storage", 1): 1.0,  # = max capacity -> constr satisfied
            ("steam_storage", 2): 2.0,  # > max capacity -> constr fails
            ("elec_storage", 0): 1.0,  # < max capacity -> constr satisfied
            ("elec_storage", 1): 2.0,  # = max capacity -> constr satisfied
            ("elec_storage", 2): 3.0,  # > max capacity -> constr fails
        }
    )

    # Expected results
    expected_soc_limit_result = {
        ("steam_storage", 0): True,
        ("steam_storage", 1): True,
        ("steam_storage", 2): False,
        ("elec_storage", 0): True,
        ("elec_storage", 1): True,
        ("elec_storage", 2): False,
    }

    # Verify constraint
    check_constraint(m, "soc_limit", False, expected_soc_limit_result)


def test_add_objective(add_constraints_setup):
    # Call the method under test
    add_constraints_setup._add_objective()

    obj = add_constraints_setup.model.objective

    # Just check that the maximizing objective was added and that it has a rule (hard to do much more here)
    assert isinstance(obj, pyo.Objective)
    assert obj.rule is not None
    assert not obj.is_minimizing()


def test_build(create_example_system):
    # Set up the builder
    builder_cls = BUILDER_REGISTRY["price_taker"]
    builder = builder_cls(create_example_system)

    # Call the method under test
    returned = builder.build()

    # Check that model and system were added
    assert isinstance(builder.model, pyo.ConcreteModel)
    assert builder.model.system is create_example_system

    # Check that sets were added
    expected_set_names = ["STORAGE", "NON_STORAGE", "R", "T"]

    for set_name in expected_set_names:
        pyo_set = getattr(builder.model, set_name, None)
        assert pyo_set is not None
        assert isinstance(pyo_set, pyo.Set)

    # Check that vars were added
    expected_var_names = ["flow", "soc", "charge", "discharge"]

    for var_name in expected_var_names:
        pyo_var = getattr(builder.model, var_name, None)
        assert pyo_var is not None
        assert isinstance(pyo_var, pyo.Var)

    # Check that constraints were added
    expected_constr_names = [
        "transfer",
        "max_capacity",
        "min_capacity",
        "resource_balance",
        "storage_balance",
        "charge_limit",
        "discharge_limit",
        "soc_limit",
    ]

    for constr_name in expected_constr_names:
        pyo_constr = getattr(builder.model, constr_name, None)
        assert pyo_constr is not None
        assert isinstance(pyo_constr, pyo.Constraint)

    # Check that objective was added
    pyo_obj = getattr(builder.model, "objective", None)
    assert pyo_obj is not None
    assert isinstance(pyo_obj, pyo.Objective)

    # Check return value
    assert returned is builder


def test_extract_results(create_example_system):
    # Finish setup of builder
    builder_cls = BUILDER_REGISTRY["price_taker"]
    builder = builder_cls(create_example_system)
    builder.build()

    m = builder.model

    # Set up example of a solved model

    # Set up flow
    m.flow.set_values(
        {
            ("elec_sink", "electricity", 0): 0.5,
            ("elec_sink", "electricity", 1): 0.5,
            ("elec_sink", "electricity", 2): 0.5,
            ("elec_sink", "steam", 0): None,
            ("elec_sink", "steam", 1): None,
            ("elec_sink", "steam", 2): None,
            ("steam_source", "electricity", 0): None,
            ("steam_source", "electricity", 1): None,
            ("steam_source", "electricity", 2): None,
            ("steam_source", "steam", 0): 1.0,
            ("steam_source", "steam", 1): 1.5,
            ("steam_source", "steam", 2): 1.0,
            ("steam_to_elec_converter", "electricity", 0): 0.5,
            ("steam_to_elec_converter", "electricity", 1): 0.5,
            ("steam_to_elec_converter", "electricity", 2): 0.5,
            ("steam_to_elec_converter", "steam", 0): 1.0,
            ("steam_to_elec_converter", "steam", 1): 1.0,
            ("steam_to_elec_converter", "steam", 2): 1.0,
        }
    )

    # Set up charge and discharge
    m.charge.set_values(
        {
            ("elec_storage", 0): 0.0,
            ("elec_storage", 1): 0.0,
            ("elec_storage", 2): 0.0,
            ("steam_storage", 0): 0.5,
            ("steam_storage", 1): 1.0,
            ("steam_storage", 2): 0.5,
        }
    )

    # Set up charge, discharge, and soc
    m.discharge.set_values(
        {
            ("elec_storage", 0): 0.0,
            ("elec_storage", 1): 0.0,
            ("elec_storage", 2): 0.0,
            ("steam_storage", 0): 0.5,
            ("steam_storage", 1): 0.5,
            ("steam_storage", 2): 0.5,
        }
    )

    m.soc.set_values(
        {
            ("elec_storage", 0): 0.0,
            ("elec_storage", 1): 0.0,
            ("elec_storage", 2): 0.0,
            ("steam_storage", 0): 0.0,
            ("steam_storage", 1): 0.5,
            ("steam_storage", 2): 0.5,
        }
    )

    m.objective.set_value(0.0)

    # Call the method under test
    actual_data = builder.extract_results()

    # Expected result

    expected_data = pd.DataFrame(
        {
            "steam_source_steam_produces": [1.0, 1.5, 1.0],
            "steam_to_elec_converter_electricity_produces": [0.5, 0.5, 0.5],
            "steam_to_elec_converter_steam_consumes": [-1.0, -1.0, -1.0],
            "elec_sink_electricity_consumes": [-0.5, -0.5, -0.5],
            "steam_storage_SOC": [0.0, 0.5, 0.5],
            "steam_storage_charge": [0.5, 1.0, 0.5],
            "steam_storage_discharge": [0.5, 0.5, 0.5],
            "elec_storage_SOC": [0.0, 0.0, 0.0],
            "elec_storage_charge": [-0.0, 0.0, 0.0],
            "elec_storage_discharge": [0.0, 0.0, 0.0],
            "objective": [0.0, 0.0, 0.0],
        }
    )

    assert actual_data.equals(expected_data)
