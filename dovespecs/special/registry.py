# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Interaction Input Specification
"""

SPECIAL_SPECS_REGISTRY: dict[str, type] = {}

def register_spec(cls):
    """
    """
    name = getattr(cls, "node_name", None)
    if name:
        SPECIAL_SPECS_REGISTRY[name] = cls
    return cls
