# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Input Specification
"""
import xml.etree.ElementTree as ET

from ravenframework.utils.InputData import InputTypes

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

if __name__ == "__main__":
  xml1 = """
<Component name="npp">
<produces resource="steam" dispatch="fixed" consumes="electricity">
<capacity>10</capacity>
</produces>
<economics lifetime="10">
<CashFlow name="capex" type="one-time">
<driver>10</driver>
<reference_price>50</reference_price>
</CashFlow>
</economics>
</Component>
"""
  # try:
  spec = ComponentSpec.getInputSpecification()()
  spec.parseNode(ET.fromstring(xml1))
  component = spec.instantiate()
  print(component)
  print(spec.generateLatex())
  # except Exception:
  #   print("Something went wrong")
