# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
from ravenframework.EntityFactoryBase import EntityFactory
from ravenframework.utils import InputData

from .polynomial import Polynomial
from .ratio import Ratio


class TransferFuncFactory(EntityFactory):
  """
  Factory for Transfer Functions
  """

  def make_input_specs(self, name, descr=None):
    """
    Fill input specs for the provided name and description.
    @ In, name, str, name of new spec
    @ In, descr, str, optional, description of spec
    @ Out, spec, InputData, specification
    """
    add_descr = ""
    if descr is None:
      description = add_descr
    else:
      description = descr + r"""\\ \\""" + add_descr

    spec = InputData.parameterInputFactory(name, descr=description)
    for name, klass in self._registeredTypes.items():
      sub_spec = klass.get_input_specs()
      sub_spec.name = name
      spec.addSub(sub_spec)
    return spec


factory = TransferFuncFactory("TransferFunc")

# fixed in inner
factory.registerType("ratio", Ratio)
factory.registerType("linear", Ratio)
factory.registerType("poly", Polynomial)
