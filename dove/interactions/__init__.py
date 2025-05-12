# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.interactions``
=====================

A dove interaction describes the role a ``dove.component``
plays within a specified energy system. These interactions
can be organized into three kinds: a producer, a storer, and a demander.
Each kind of interaction has different capabilities and associated data.

Interaction
------------
The abstract base class for all interaction types.

This class contains general technical information that all interaction
types have. For example, the capacity of a component is an attribute shared
across all three interaction types.

All interactions are governed by the resource(s) they defined to deal in.
For example, a producing component may consume 'steam' and output 'electricity.'

Producer
------------
A producer is a component that can be a source node within the system or
a node that consumes a resource and ouputs a resource.

Producer is the only kind of interaction to be able to consume multiple
resources and produce a single resource or consume no resources at all and
produce a resource.

Transfer functions are required to be defined for types of producers that
consume a resource and produce a different kind of resource. Transfer functions
are defined and documented in the ``dove.physics`` module.

Storage
------------
A storer is a component that can consume a single resource and output a single
resource at a later point in time.

Demand
------------
A demander is an interaction that simply demands a particular resource.

These interaction types can be thought of as sinks to the defined problem.
"""

# only type references here, as needed
from .interaction import Interaction
from .demands import Demand
from .produces import Producer
from .stores import Storage

__all__ = ["Interaction", "Producer", "Storage", "Demand"]
