# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.models.base``
========================

Base module providing abstract base classes for model builders in the DOVE system.

This module defines the foundation for all model builders, which are responsible
for creating, solving, and extracting results from computational models.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dove.core.system import System


class BaseModelBuilder(ABC):
    """
    Abstract base class for all model builders in the DOVE system.

    This class defines the interface that all model builders must implement,
    providing a consistent workflow for building, solving, and extracting
    results from models.

    Attributes
    ----------
    system : System
        Reference to the DOVE system instance.
    model : Any
        The constructed model object (initialized to None).
    """

    def __init__(self, system: "System") -> None:
        """
        Initialize a model builder.

        Parameters
        ----------
        system : System
            Reference to the DOVE system instance.
        """
        self.system = system
        self.model: Any = None

    @abstractmethod
    def build(self) -> Any:
        """
        Build a model based on the system configuration.

        This method should create and populate the model structure
        based on the current system state.

        Returns
        -------
        Any
            The built model object.
        """
        ...

    @abstractmethod
    def solve(self) -> Any:
        """
        Solve the built model.

        This method should execute the model and obtain solutions
        for the problem defined in the model.

        Returns
        -------
        Any
            The solution or results from solving the model.
        """
        ...

    @abstractmethod
    def extract_results(self) -> Any:
        """
        Extract and process results from the solved model.

        This method should convert the raw model solution into a
        format usable by the rest of the DOVE system.

        Returns
        -------
        Any
            The processed results from the model.
        """
        ...
