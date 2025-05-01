# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Interaction Input Specification
"""

from typing import Any
from ravenframework.utils.InputData import parameterInputFactory

from dovespecs.autospec import AutoSpec


class SimpleNodeSpec(AutoSpec):
  """ """

  node_name: str
  content_type: type
  params: dict[str, tuple] = {}
  description: str = ""

  @classmethod
  def getInputSpecification(cls):
    """ """
    Base = parameterInputFactory(cls.node_name, contentType=cls.content_type, descr=cls.description)
    Mixin = type(f"{cls.node_name.capitalize()}Spec", (SimpleNodeSpec, Base), {})
    for pname, (ptype, preq, pdef, pdescr) in cls.params.items():
      Mixin.addParam(pname, param_type=ptype, required=preq, default=pdef, descr=pdescr)
    return Mixin

  def instantiate(self) -> dict[str, Any]: # type: ignore # noqa: D102
    return {**self.parameterValues, "value": self.value}
