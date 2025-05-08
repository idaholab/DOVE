# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dove.core.system import System


class BaseModelBuilder(ABC):
    """ """

    def __init__(self, system: "System") -> None:
        """ """
        self.system = system
        self.model: Any = None

    @abstractmethod
    def build(self) -> Any:
        """ """
        ...

    @abstractmethod
    def solve(self) -> Any:
        """ """
        ...

    @abstractmethod
    def extract_results(self) -> Any:
        """ """
        ...
