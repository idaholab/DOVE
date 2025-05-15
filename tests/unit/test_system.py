# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import pytest

from dove.core import Resource, Source
from dove.core.system import System


def test_system_initialization_empty():
    sys = System()
    assert isinstance(sys.components, list)
    assert sys.components == []
    assert isinstance(sys.resources, list)
    assert sys.resources == []


# def test_add_and_get_components_and_resources():
#   sys = System()
#   r_w = Resource(name="water")
#   r_e = Resource(name="electricity")
#   src = Source(name="src", max_capacity=10.0, produces=r_w)
#   sink = Sink(name="sink", max_capacity=5.0, consumes=r_w)
#   conv = Converter(name="conv", max_capacity=8.0, consumes=[r_w], produces=[r_e])
#   sys.add_component(src)
#   sys.add_component(sink)
#   sys.add_component(conv)

#   # components list updated
#   assert src in sys.components
#   assert sink in sys.components
#   assert conv in sys.components

#   # resources registered
#   assert "water" in sys.resources
#   assert "electricity" in sys.resources
#   assert sys.resources["water"] is r_w
#   assert sys.resources["electricity"] is r_e


def test_adding_duplicate_component_name_raises():
    sys = System()
    r = Resource(name="res")
    c1 = Source(name="c", produces=r, max_capacity=1.0, min_capacity=0.0, profile=[0.1])
    c2 = Source(name="c", produces=r, max_capacity=2.0, min_capacity=0.0, profile=[0.2])
    sys.add_component(c1)
    with pytest.raises(ValueError):
        sys.add_component(c2)


# def test_remove_component_and_resource_cleanup():
#   sys = System()
#   r = Resource(name="resA")
#   src = Source(name="srcA", max_capacity=3.0, produces=r)
#   sys.add_component(src)
#   sys.remove_component("srcA")
#   assert src not in sys.components
#   # resource still in system? implementation choice: assume removal if unused
#   assert "resA" not in sys.resources


# def test_system_summary_dict():
#   sys = System()
#   r = Resource(name="resB")
#   src = Source(name="srcB", max_capacity=4.0, produces=r)
#   sink = Sink(name="sinkB", max_capacity=2.0, consumes=r)
#   sys.add_component(src)
#   sys.add_component(sink)
#   summary = sys.summary()
#   assert isinstance(summary, dict)
#   assert "components" in summary and isinstance(summary["components"], list)
#   names = [c["name"] for c in summary["components"]]
#   assert set(names) == {"srcB", "sinkB"}
#   assert "resources" in summary and "resB" in summary["resources"]


# def test_run_without_components_returns_empty():
#   sys = System(name="empty_run")
#   result = sys.run()
#   # Expect result to be an empty array or dict, depending on impl
#   assert result is not None


# def test_run_simple_flow_produces_expected_profile():
#   sys = System(name="flow_sys")
#   r = Resource(name="resC")
#   profile = [1.0, 0.5, 0.0]
#   src = Source(name="srcC", max_capacity=5.0, produces=r, profile=profile)
#   sink = Sink(name="sinkC", max_capacity=5.0, consumes=r)
#   sys.add_component(src)
#   sys.add_component(sink)
#   timeline = sys.run()
#   # Assuming run returns a time-series dict of resource balances
#   assert hasattr(timeline, "shape") or isinstance(timeline, dict)


# def test_optimizer_integration_placeholder():
#   sys = System(name="opt_sys")
#   # This is a placeholder for testing optimizer integration
#   # e.g. sys.optimize(), check it returns optimal dispatch
#   assert hasattr(sys, "optimize")
#   with pytest.raises(NotImplementedError):
#     sys.optimize()
