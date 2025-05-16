# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.resource``
=======================

This module provides the Resource class for representing and managing system resources.
Resources are fundamental entities that can be allocated, tracked, and managed within
the DOVE system. Each resource is identified by a unique name and can optionally have
an associated unit of measurement.

Classes:
    Resource: A dataclass representing a system resource with a name and optional unit.

Example:
    ```
    # Create a resource for electricity with kilowatt-hours as unit
    electricity = Resource(name="electricity", unit="kWh")

    # Create a resource without a specific unit
    labor = Resource(name="labor")
    ```
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    """
    A class representing a resource in the system.

    This class is used to model resources that can be allocated, managed, or tracked
    within the system. Each resource has a name and an optional unit of measurement.

    Attributes:
        name (str): The unique name of the resource.
        unit (str | None): The unit of measurement for the resource (e.g., "kg", "liters", "pieces").
            Defaults to None if the resource doesn't have a specific unit. (Currently not used)
    """

    name: str
    unit: str | None = None
