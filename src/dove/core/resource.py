# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    """ """

    name: str
    unit: str | None = None
