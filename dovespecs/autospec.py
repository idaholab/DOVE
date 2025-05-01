# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Auto Spec Base Class
"""

from collections import defaultdict

from ravenframework.utils.InputData import ParameterInput


class AutoSpec(ParameterInput):
  """ """

  associated_class: type

  def parseNode(self, node, errorList=None, parentList=None) -> None:
    """ """
    super().parseNode(node, errorList, parentList)

    for child in self.subparts:
      print(child)
      child.parent = self

    self.validate()

  def validate(self) -> None:
    """ """
    pass

  def instantiate(self) -> object:
    """ """
    pass
