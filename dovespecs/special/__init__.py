# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dovespecs.special``
======================
"""

from .capacity_spec import CapacitySpec
from .capacity_factor_spec import CapacityFactorSpec
from .minimum_spec import MinimumSpec
from .initial_stored_spec import InitialStoredSpec
from .strategy_spec import StrategySpec
from .driver_spec import DriverSpec
from .ref_price_spec import ReferencePriceSpec
from .ref_driver_spec import ReferenceDriverSpec
from .scaling_factor_spec import ScalingFactorSpec


from .registry import SPECIAL_SPECS_REGISTRY as SS_REGISTRY

__all__ = [
  "CapacitySpec",
  "CapacityFactorSpec",
  "MinimumSpec",
  "InitialStoredSpec",
  "StrategySpec",
  "DriverSpec",
  "ReferencePriceSpec",
  "ReferenceDriverSpec",
  "ScalingFactorSpec",
  "SS_REGISTRY"
]
