# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Resource:
    """ """

    name: str
    unit: Optional[str] = None
