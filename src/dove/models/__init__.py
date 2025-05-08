# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """
from typing import Type

BUILDER_REGISTRY: dict[str, Type] = {}

def register_builder(name: str):
    """ """
    def _decorator(cls: Type):
        BUILDER_REGISTRY[name] = cls
    return _decorator

from .price_taker import PriceTakerBuilder

__all__ = ["BUILDER_REGISTRY", "PriceTakerBuilder"]
