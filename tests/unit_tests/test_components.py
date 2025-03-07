import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY
import xml.etree.ElementTree as ET

from ravenframework.utils import InputData

from DOVE.src.Components import Component



class TestComponent(unittest.TestCase):
  def setUp(self):
    # Create patchers
    parameter_input_factory_patcher = patch("ravenframework.utils.InputData.parameterInputFactory")
    producer_patcher = patch("DOVE.src.Components.Producer")
    storage_patcher = patch("DOVE.src.Components.Storage")
    demand_patcher = patch("DOVE.src.Components.Demand")
    cashflow_patcher = patch("DOVE.src.Components.CashFlowGroup")

    # Start patchers and store mocks
    self.mock_parameter_input_factory = parameter_input_factory_patcher.start()
    self.mock_producer = producer_patcher.start()
    self.mock_storage = storage_patcher.start()
    self.mock_demand = demand_patcher.start()
    self.mock_cashflow = cashflow_patcher.start()

    # Add cleanup to stop manually started patchers
    self.addCleanup(patch.stopall)

    # Set up mocks
    self.mock_specs = MagicMock()
    self.mock_parameter_input_factory.return_value = self.mock_specs

    self.mock_prod_specs = MagicMock(name="ProducerSpecs")
    self.mock_stor_specs = MagicMock(name="StorageSpecs")
    self.mock_demand_specs = MagicMock(name="DemandSpecs")
    self.mock_cashflow_specs = MagicMock(name="CashFlowSpecs")

    self.mock_producer.get_input_specs.return_value = self.mock_prod_specs
    self.mock_storage.get_input_specs.return_value = self.mock_stor_specs
    self.mock_demand.get_input_specs.return_value = self.mock_demand_specs
    self.mock_cashflow.get_input_specs.return_value = self.mock_cashflow_specs

  def test_get_input_specs(self):
    # Call the method under test
    specs = Component.get_input_specs()

    # Assertions to verify behavior
    self.mock_parameter_input_factory.assert_called_once_with(
      "Component", ordered=False, baseNode=None, descr=ANY
    )

    # Check if the 'name' parameter was added correctly
    self.mock_specs.addParam.assert_called_once_with(
      "name", param_type=InputData.InputTypes.StringType, required=True, descr=ANY
    )

    # Check that all sub-specifications were added
    expected_calls = [
      call(self.mock_prod_specs),
      call(self.mock_stor_specs),
      call(self.mock_demand_specs),
      call(self.mock_cashflow_specs),
    ]
    self.mock_specs.addSub.assert_has_calls(expected_calls, any_order=True)

    # Check the returned value
    self.assertEqual(specs, self.mock_specs)

  def test_read_input(self):
    # Note that this test also checks the handler functions and get_interaction
    test_xml_str = """<DOVE>
                        <Component name="comp1">
                          <produces></produces>
                        </Component>
                      </DOVE>"""
    test_xml_tree = ET.ElementTree(ET.fromstring(test_xml_str))
    comp1_node = test_xml_tree.find('./Component[@name="comp1"]')

    # Additional mock info
    self.mock_specs.return_value.parameterValues = {"name": "comp1"}
    mock_comp1_prod = MagicMock()
    mock_comp1_prod.getName.return_value = "produces"
    self.mock_specs.return_value.subparts = [mock_comp1_prod]

    # Call the method under test
    test_component = Component()
    test_component.read_input(comp1_node)

    # Checks for read_input
    self.mock_specs.return_value.parseNode.assert_called_once_with(comp1_node)
    self.assertIs(test_component.name, "comp1")

    # Checks for handle_produces
    self.mock_producer.assert_called_once_with(messageHandler=test_component.messageHandler)
    self.mock_producer.return_value.read_input.assert_called_once_with(mock_comp1_prod, "comp1")
    self.assertIs(test_component.get_interaction(), self.mock_producer.return_value)


if __name__ == "__main__":
  unittest.main()
