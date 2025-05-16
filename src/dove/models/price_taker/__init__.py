# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.models.price_taker``
========================

Price Taker model building functionality.

This module provides tools for building and configuring price taker models
within the DOVE framework. Price taker models represent entities that accept
market prices as given without influencing them.

Classes
-------
PriceTakerBuilder
  Builder class for creating and configuring price taker models.
"""

from .builder import PriceTakerBuilder

__all__ = ["PriceTakerBuilder"]
