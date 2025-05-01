# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Input Specification
"""
import xml.etree.ElementTree as ET

from ravenframework.utils.InputData import InputTypes, parseFromList

from dove import Component

from .autospec import AutoSpec
from .interaction_spec import DemandSpec, ProducerSpec, StorageSpec
from .economics_spec import EconomicSpec


class ComponentSpec(AutoSpec):
  """
  """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """
    """
    cls.createClass(
      "Component",
      ordered=False,
      baseNode=None,
      descr=r"""
      defines a component as an element of the grid system.
      Components are defined by the action they perform such as
      \xmlNode{produces} or \xmlNode{consumes}; see details below.
      """,
    )

    cls.addParam(
      "name",
      param_type=InputTypes.StringType,
      required=True,
      descr=r"""
      identifier for the component. This identifier will be used to
      generate variables and relate signals to this component throughout
      the DOVE analysis.
      """,
    )

    cls.addSub(ProducerSpec.getInputSpecification())
    cls.addSub(DemandSpec.getInputSpecification())
    cls.addSub(StorageSpec.getInputSpecification())
    cls.addSub(EconomicSpec.getInputSpecification())
    cls.associated_class = Component

    return cls
  
  def instantiate(self) -> object:
    pass

if __name__ == "__main__":
  xml1 = """
<Component name="npp">
<produces resource="steam" dispatch="fixed" consumes="electricity">
  <capacity>10</capacity>
  <capacity_factor>0.5</capacity_factor>
  <transfer>
      <ratio>
        <rate resource="steam">10</rate>
        <rate resource="electricity">11</rate>
      </ratio>
  </transfer>
</produces>
  <economics lifetime="10">
    <CashFlow name="capex" type="one-time">
        <driver>10</driver>
        <reference_price levelized="True">50</reference_price>
        <reference_driver>10</reference_driver>
        <scaling_factor_x>1</scaling_factor_x>
    </CashFlow>
  </economics>
</Component>
"""
  # spec = ComponentSpec.getInputSpecification()()
  # spec.parseNode(ET.fromstring(xml1))
  spec = parseFromList(ET.fromstring(xml1), [ComponentSpec.getInputSpecification(),
                                             ProducerSpec.getInputSpecification()])
  component = spec.instantiate()
  print(component)
  print(spec.generateLatex())

