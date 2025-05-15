# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

TimeDependent: TypeAlias = list[float] | NDArray[np.float64]


@dataclass
class CashFlow(ABC):
    """ """

    name: str
    price_profile: TimeDependent = field(default_factory=list)
    alpha: float = 1.0
    dprime: float = 1.0
    scalex: float = 1.0
    price_is_levelized: bool = False
    sign: int = 0


@dataclass
class Cost(CashFlow):
    """ """

    sign: int = -1


@dataclass
class Revenue(CashFlow):
    """ """

    sign: int = +1
