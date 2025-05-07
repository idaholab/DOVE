# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove``
=========

The Dispatch Optimization Variable Engine (DOVE) is a library used to configure
energy system components and compute an optimized dispatch strategy for resources
throughout the system.
"""

from .components import Component


__all__ = [
  "Component",
]
