# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Model registry and builder pattern implementation for DOVE.

This module provides a registry system for model builders in the DOVE framework.
It allows different model building strategies to be registered and retrieved by name.

The module defines:
    - BUILDER_REGISTRY: A dictionary mapping model builder names to their classes
    - register_builder: A decorator for registering model builder classes

Examples
--------
To register a new model builder:
    ```
    @register_builder("my_model")
    class MyModelBuilder(BaseModelBuilder):
        ...
    ```

To access a registered builder:
    ```
    builder_cls = BUILDER_REGISTRY["my_model"]
    builder = builder_cls(...)
    ```
"""

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
