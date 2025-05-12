# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove``
=========

The Dispatch Optimization Variable Engine (DOVE) is a library used to configure
energy system components and compute an optimized dispatch strategy for resources
throughout the system.
"""
from importlib.util import find_spec

# ravenframework could be pip-installed or located elsewhere.
if find_spec("ravenframework") is None:
  import sys
  from .utils import get_raven_loc
  # Add ravenframework to the PYTHONPATH
  sys.path.append(get_raven_loc())

from .components import Component
from .economics import CashFlow, CashFlowGroup
from .interactions import Demand, Interaction, Producer, Storage

__all__ = [
  "Component",
  "Interaction",
  "Producer",
  "Storage",
  "Demand",
  "CashFlow",
  "CashFlowGroup",
]
