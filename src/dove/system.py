# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

from typing import Self


class System:
    """ """

    def __init__(self, components: list, resources: list) -> None:
        """ """
        self.components: list = components
        self.resources: list = resources

    def add_component(self, comp) -> Self:
        """ """
        self.components.append(comp)
        return self

    def add_resource(self, res) -> Self:
        """ """
        self.resources.append(res)
        return self

    def build(self) -> None:
        """ """
        pass

    def solve(self) -> None:
        """ """
        pass
