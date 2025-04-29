# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
# import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
import xml.etree.ElementTree as ET
from unittest.mock import ANY, MagicMock, call, patch

# Add dove to python path
import resolve_module_path  # noqa: F401

# import dove before ravenframework
from dove import Component
from ravenframework.utils import InputData


class TestComponent(unittest.TestCase):
  # For convenience, patches and mocks that are needed for all tests are set up here
  def setUp(self):
    # Create patchers
    parameterInputFactoryPatcher = patch("ravenframework.utils.InputData.parameterInputFactory")
    producerPatcher = patch("dove.Producer")
    storagePatcher = patch("dove.Storage")
    demandPatcher = patch("dove.Demand")
    cashflowPatcher = patch("dove.CashFlowGroup")

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()
    self.mockProducer = producerPatcher.start()
    self.mockStorage = storagePatcher.start()
    self.mockDemand = demandPatcher.start()
    self.mockCashflow = cashflowPatcher.start()

    # Add cleanup to stop manually started patchers
    self.addCleanup(patch.stopall)

    # Set up mocks
    self.mockSpecs = MagicMock()
    self.mockParameterInputFactory.return_value = self.mockSpecs

    self.mockProdSpecs = MagicMock(name="ProducerSpecs")
    self.mockStorSpecs = MagicMock(name="StorageSpecs")
    self.mockDemandSpecs = MagicMock(name="DemandSpecs")
    self.mockCashflowSpecs = MagicMock(name="CashFlowSpecs")

    self.mockProducer.get_input_specs.return_value = self.mockProdSpecs
    self.mockStorage.get_input_specs.return_value = self.mockStorSpecs
    self.mockDemand.get_input_specs.return_value = self.mockDemandSpecs
    self.mockCashflow.get_input_specs.return_value = self.mockCashflowSpecs

  def testGetInputSpecs(self):
    # Call the method under test
    specs = Component.get_input_specs()

    # Assertions to verify behavior
    self.mockParameterInputFactory.assert_called_once_with(
      "Component", ordered=False, baseNode=None, descr=ANY
    )

    # Check if the 'name' parameter was added correctly
    self.mockSpecs.addParam.assert_called_once_with(
      "name", param_type=InputData.InputTypes.StringType, required=True, descr=ANY
    )

    # Check that all sub-specifications were added
    expectedCalls = [
      call(self.mockProdSpecs),
      call(self.mockStorSpecs),
      call(self.mockDemandSpecs),
      call(self.mockCashflowSpecs),
    ]
    self.mockSpecs.addSub.assert_has_calls(expectedCalls, any_order=True)

    # Check the returned value
    self.assertEqual(specs, self.mockSpecs)

  def testReadInput(self):
    # Note that this test also checks the handler functions and get_interaction

    # Set up xml
    # comp1 => produces
    # comp2 => stores
    # comp3 => demands
    # comp4 => economics
    # comp5 => no subnodes that read_input cares about
    # comp6 => produces AND demands, which is bad input and should throw an error
    testXMLstr = """<DOVE>
                        <Component name="comp1">
                          <produces>this_node_doesn't_actually_matter</produces>
                        </Component>
                        <Component name="comp2">
                          <stores>all_these_get_mocked</stores>
                        </Component>
                        <Component name="comp3">
                          <demands>including_this_one</demands>
                        </Component>
                        <Component name="comp4">
                          <economics>and_this_one</economics>
                        </Component>
                        <Component name="comp5">
                          <other_comp_subnode>and_also_this_one</other_comp_subnode>
                        </Component>

                        <Component name="comp6">
                          <produces>same_as_above</produces>
                          <demands>for_both_of_these</demands>
                        </Component>
                      </DOVE>"""
    testXMLTree = ET.ElementTree(ET.fromstring(testXMLstr))

    # Find ET.Element for each component
    comp1Node = testXMLTree.find('./Component[@name="comp1"]')
    comp2Node = testXMLTree.find('./Component[@name="comp2"]')
    comp3Node = testXMLTree.find('./Component[@name="comp3"]')
    comp4Node = testXMLTree.find('./Component[@name="comp4"]')
    comp5Node = testXMLTree.find('./Component[@name="comp5"]')
    comp6Node = testXMLTree.find('./Component[@name="comp6"]')

    # Mock setup for subnodes

    mockProducesNode = MagicMock()
    mockProducesNode.getName.return_value = "produces"

    mockStoresNode = MagicMock()
    mockStoresNode.getName.return_value = "stores"

    mockDemandsNode = MagicMock()
    mockDemandsNode.getName.return_value = "demands"

    mockEconomicsNode = MagicMock()
    mockEconomicsNode.getName.return_value = "economics"

    mockOtherCompSubnode = MagicMock()
    mockOtherCompSubnode.getName.return_value = "other_comp_subnode"

    # For comps 1-5: Set up component-specific mock info,
    # create test components, and call the method under test

    self.mockSpecs.return_value.parameterValues = {"name": "comp1"}
    self.mockSpecs.return_value.subparts = [mockProducesNode]
    testComp1 = Component()
    testComp1.read_input(comp1Node)

    self.mockSpecs.return_value.parameterValues = {"name": "comp2"}
    self.mockSpecs.return_value.subparts = [mockStoresNode]
    testComp2 = Component()
    testComp2.read_input(comp2Node)

    self.mockSpecs.return_value.parameterValues = {"name": "comp3"}
    self.mockSpecs.return_value.subparts = [mockDemandsNode]
    testComp3 = Component()
    testComp3.read_input(comp3Node)

    self.mockSpecs.return_value.parameterValues = {"name": "comp4"}
    self.mockSpecs.return_value.subparts = [mockEconomicsNode]
    testComp4 = Component()
    testComp4.read_input(comp4Node)

    self.mockSpecs.return_value.parameterValues = {"name": "comp5"}
    self.mockSpecs.return_value.subparts = [mockOtherCompSubnode]
    testComp5 = Component()
    testComp5.read_input(comp5Node)

    # Checks for read_input

    # Check that component nodes were parsed
    expectedParseNodeCalls = [
      call(comp1Node),
      call(comp2Node),
      call(comp3Node),
      call(comp4Node),
      call(comp5Node)
    ]
    self.mockSpecs.return_value.parseNode.assert_has_calls(expectedParseNodeCalls)

    # Check that names were set correctly
    self.assertIs(testComp1.name, "comp1")
    self.assertIs(testComp2.name, "comp2")
    self.assertIs(testComp3.name, "comp3")
    self.assertIs(testComp4.name, "comp4")
    self.assertIs(testComp5.name, "comp5")

    # Checks for handle_produces
    self.mockProducer.assert_called_once_with(messageHandler=testComp1.messageHandler)
    self.mockProducer.return_value.read_input.assert_called_once_with(mockProducesNode, "comp1")
    self.assertIs(testComp1.interaction, self.mockProducer.return_value)

    # Checks for handle_stores
    self.mockStorage.assert_called_once_with(messageHandler=testComp2.messageHandler)
    self.mockStorage.return_value.read_input.assert_called_once_with(mockStoresNode, "comp2")
    self.assertIs(testComp2.interaction, self.mockStorage.return_value)

    # Checks for handle_demands
    self.mockDemand.assert_called_once_with(messageHandler=testComp3.messageHandler)
    self.mockDemand.return_value.read_input.assert_called_once_with(mockDemandsNode, "comp3")
    self.assertIs(testComp3.interaction, self.mockDemand.return_value)

    # Checks for handle_economics
    self.mockCashflow.assert_called_once_with(messageHandler=testComp4.messageHandler)
    self.mockCashflow.return_value.read_input.assert_called_once_with(mockEconomicsNode)
    self.assertIs(testComp4.economics, self.mockCashflow.return_value)

    # comp5 should call none of the handlers
    # If it did call a handler, it would be caught above

    # Now check that the bad component causes an error
    self.mockSpecs.return_value.parameterValues = {"name": "comp6"}
    self.mockSpecs.return_value.subparts = [mockProducesNode, mockDemandsNode] # Both is bad
    testComp6 = Component()
    with self.assertRaises(NotImplementedError):
      testComp6.read_input(comp6Node)

if __name__ == "__main__":
  unittest.main()
