# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Input Specification
"""
from collections import defaultdict
import xml.etree.ElementTree as ET

from ravenframework.utils.InputData import InputTypes

from dove.components import Producer, Storage, Demand, CashFlow, ResourceSpec

from .autospec import AutoSpec
from .producer_spec import ProducerSpec
from .storage_spec import StorageSpec
from .demand_spec import DemandSpec
from .economics_spec import EconomicSpec


class ComponentSpec(AutoSpec):
  """ """

  @classmethod
  def getInputSpecification(cls) -> type[AutoSpec]:
    """ """
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

    return cls

  def _parse_req_interaction_values(self, spec):
    """
    """
    return_kwargs = {}
    attr = spec.parameterValues
    return_kwargs["dispatch_flexibility"] = attr.get("dispatch", None)

    capacity = spec.findFirst("capacity")
    minimum = spec.findFirst("minimum")
    capacity_factor = spec.findFirst("capacity_factor")

    if capacity is not None:
        capacity = capacity.instantiate()
        return_kwargs["capacity_var"] = capacity.get("resource", None)
        return_kwargs["capacity"] = capacity.get("value", None)

    if capacity_factor is not None:
      capacity_factor = capacity_factor.instantiate()
      return_kwargs["capacity_factor"] = capacity_factor["value"]

    if minimum is not None:
      minimum = minimum.instantiate()
      return_kwargs["minimum_var"] = minimum.get("resource", None)
      return_kwargs["minimum"] = minimum["value"]

    return return_kwargs

  def instantiate(self) -> Producer | Storage | Demand:
    """ """
    interaction_map = {
      "produces": Producer,
      "stores": Storage,
      "demands": Demand
    }
    comp_name = self.parameterValues["name"]

    for child in self.subparts:
      match (role := child.getName()):
        case "produces" | "stores" | "demands":
          comp_obj = interaction_map[role]
          comp_vars = self._parse_req_interaction_values(child)
          specific_vars = child.instantiate()
          comp_vars.update(specific_vars)
          filtered = {k: v for k, v in comp_vars.items() if v is not None}
          comp_vars.clear()
          comp_vars.update(filtered)

        case "economics":
          comp_vars["lifetime"] = child.parameterValues.get("lifetime")
          cfs = []
          cashflow_args = defaultdict(dict)
          for cfg in child.findAll("CashFlow"):
            cfg_attr = cfg.parameterValues
            cashflow_args["name"] = cfg_attr["name"]
            cashflow_args["category"] = cfg_attr["type"]
            cashflow_args["is_taxable"] = cfg_attr.get("taxable", True)
            cashflow_args["has_inflation"] = cfg_attr.get("inflation", None)
            cashflow_args["is_npv_exempt"] = cfg_attr.get("npv_exempt", None)
            cashflow_args["period"] = cfg_attr.get("period", None)
            cashflow_args["depreciation"] = cfg_attr.get("depreciate", None)

            driver = cfg.findFirst("driver")
            ref_price = cfg.findFirst("reference_price")
            ref_driver = cfg.findFirst("reference_driver")
            scaling_factor = cfg.findFirst("scaling_factor_x")

            if driver is not None:
              driver = driver.instantiate()
              cashflow_args["driver"] = driver["value"]
            if ref_price is not None:
              ref_price = ref_price.instantiate()
              cashflow_args["reference_price"] = ref_price["value"]
              cashflow_args["is_price_levelized"] = ref_price.get("levelized")
            if ref_driver is not None:
              ref_driver = ref_driver.instantiate()
              cashflow_args["reference_driver"] = ref_driver["value"]
            if scaling_factor is not None:
              scaling_factor = scaling_factor.instantiate()
              cashflow_args["scaling_factor_x"] = scaling_factor["value"]

            cf = CashFlow(**cashflow_args)
            cfs.append(cf)
        case _:
          raise IOError("<Component> only accepts one of three kinds of subnodes!")

    return comp_obj(name=comp_name, **comp_vars, cashflows=cfs)

if __name__ == "__main__":
  xml1 = """
<Component name="npp">
<produces resource="steam" dispatch="fixed">
  <capacity>10</capacity>
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
  spec = ComponentSpec.getInputSpecification()()
  spec.parseNode(ET.fromstring(xml1))
  assert spec is not None
  component = spec.instantiate()
  print(component)
  for cf in component.cashflows:
    print(cf)
  # print(spec.generateLatex())
