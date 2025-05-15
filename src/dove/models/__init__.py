# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseModelBuilder

BUILDER_REGISTRY: dict[str, type["BaseModelBuilder"]] = {}


def register_builder(name: str) -> Callable[[type["BaseModelBuilder"]], None]:
    """ """

    def _decorator(cls: type["BaseModelBuilder"]) -> None:
        BUILDER_REGISTRY[name] = cls

    return _decorator


from .price_taker import PriceTakerBuilder

__all__ = ["BUILDER_REGISTRY", "PriceTakerBuilder"]
