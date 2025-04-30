# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Auto Spec Base Class
"""
from ravenframework.utils.InputData import ParameterInput

class AutoSpec(ParameterInput):
    """
    """

    def instantiate(self) -> None:
        """
        """
        return self.associated_class()
