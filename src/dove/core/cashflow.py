# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.core.cashflow``
======================

Module containing cash flow classes for financial modeling in DOVE.

This module defines classes for representing financial cash flows in energy system models,
including both costs and revenues. These cash flows can vary over time and have
configurable scaling factors.

Classes
--------
    CashFlow: Abstract base class for all cash flows
    Cost: Represents expenses or negative cash flows
    Revenue: Represents income or positive cash flows
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

TimeDependent: TypeAlias = list[float] | NDArray[np.float64]


@dataclass
class CashFlow(ABC):
    """
    Abstract base class representing a financial cash flow.

    This class serves as the foundation for different types of cash flows in the system.
    Cash flows have associated pricing profiles that can vary over time. If a price profile
    is not provided, it will default to using alpha as the fixed recurring value for the
    length of the simulation.

    Parameters
    ----------
    name : str
        Identifier for the cash flow.
    price_profile : TimeDependent, optional
        Time-dependent pricing data, defaults to empty list.
    alpha : float, optional
        Scaling factor for the cash flow magnitude, defaults to 1.0.
    dprime : float, optional
        Adjustment factor for price calculations, defaults to 1.0.
    scalex : float, optional
        Horizontal scaling factor for time-dependent functions, defaults to 1.0.
    price_is_levelized : bool, optional
        Flag indicating if the price is levelized, defaults to False. (Not Implemented)
    sign : int, optional
        Direction of the cash flow (positive or negative), defaults to 0.
    """

    name: str
    price_profile: TimeDependent = field(default_factory=list)
    alpha: float = 1.0
    dprime: float = 1.0
    scalex: float = 1.0
    price_is_levelized: bool = False
    sign: int = 0


@dataclass
class Cost(CashFlow):
    """
    Represents a negative cash flow or cost.

    This class is a subclass of the `CashFlow` abstract base class that specifically
    represents costs or expenses. A `Cost` instance always has a negative sign,
    which is enforced by setting the `sign` class attribute to -1.

    Attributes
    ----------
    sign : int
        Fixed value of -1 to indicate that this cash flow represents a cost.

    Examples
    --------
    A recurring cost of $1,000.00 per time period:

    >>> cost = Cost(name="Recurring Cost", alpha=1000.0)

    Note that not specifying a `price_profile` will default to using `alpha` as
    the fixed value for the length of the simulation.

    A time-dependent cost with a specific price profile:
    >>> cost = Cost(
    ...     name="Time-Dependent Cost",
    ...     price_profile=[0.5, 1.0, 1.5],
    ...     alpha=1000.0,)
    """

    sign: int = -1


@dataclass
class Revenue(CashFlow):
    """
    A class representing revenue in a financial context.

    Revenue is a subclass of CashFlow with a positive sign (+1), indicating
    incoming cash flow. It represents income generated from the sale of goods,
    services, or other business activities.

    Attributes
    ----------
    sign : int
        The sign of the cash flow, set to +1 for revenue (incoming cash).
    """

    sign: int = +1
