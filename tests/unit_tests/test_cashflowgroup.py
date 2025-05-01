# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
# import __init__  # Running __init__ here enables importing from DOVE and RAVEN
"""
Unit tests for ``dove.economics``
"""
import unittest
from unittest.mock import MagicMock, call, patch, ANY

# Add dove to python path
from . import resolve_module_path  # noqa: F401

# import dove before ravenframework
from dove.economics import CashFlowGroup
from ravenframework.utils import InputData, InputTypes


# from DOVE.src.Base import Base

class TestCashFlowGroup(unittest.TestCase):
  # For convenience, patches and mocks that are needed for all tests are set up here
  def setUp(self):
    # Create patchers
    parameterInputFactoryPatcher = patch("ravenframework.utils.InputData.parameterInputFactory")
    cashFlowPatcher = patch("dove.economics.CashFlow")
    #baseInitpatcher = patch.object(Base, '__init__')

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()
    self.mockCashFlow = cashFlowPatcher.start()
    #self.mockBaseInit = baseInitpatcher.start()

    # Add cleanup to stop manually started patchers
    self.addCleanup(patch.stopall)

    # Mock setup
    self.mockEconomicsParsed = MagicMock()
    self.mockLifetimeParsed = MagicMock()

  def testGetInputSpecs(self):

    # Test-specific mock setup
    self.mockParameterInputFactory.side_effect = [self.mockEconomicsParsed, self.mockLifetimeParsed]

    # Call the method under test
    specs = CashFlowGroup.get_input_specs()

    # Assertions to verify behavior
    expectedParameterInputFactoryCalls = [
      call("economics", ordered=False, baseNode=None, descr=ANY),
      call("lifetime", contentType=InputTypes.IntegerType, descr=ANY)
    ]

    self.mockParameterInputFactory.assert_has_calls(expectedParameterInputFactoryCalls)

    # Check that sub-specs were added
    expectedAddSubCalls = [
      call(self.mockLifetimeParsed),
      call(self.mockCashFlow.get_input_specs())
    ]

    self.mockEconomicsParsed.addSub.assert_has_calls(expectedAddSubCalls)

    # Check the returned value
    self.assertEqual(specs, self.mockEconomicsParsed)

  def testReadInput(self):
    # Note that this test also checks __init__, component, lifetime, and cashflows

    # Test-specific mock setup
    mockSpecs = MagicMock()

    self.mockLifetimeParsed.getName.return_value = "lifetime"
    self.mockLifetimeParsed.value = 50

    mockCFNode1 = MagicMock()
    mockCFNode1.getName.return_value = "CashFlow"

    mockCFNode2 = MagicMock()
    mockCFNode2.getName.return_value = "CashFlow"

    mockSpecs.subparts = [self.mockLifetimeParsed, mockCFNode1, mockCFNode2]

    mockNewCFInstance1 = MagicMock()
    mockNewCFInstance2 = MagicMock()
    self.mockCashFlow.side_effect = [mockNewCFInstance1, mockNewCFInstance2]

    mockComponent = MagicMock()
    mockComponent.name = "test_component"

    ### PART 1: Non-XML input

    # Call the method under test with non-xml input
    # TODO: Should CashFlowGroup.__init__ have a default for the "component" input?
    # It throws an error when none is provided
    testCashFlowGroup = CashFlowGroup(mockComponent)
    testCashFlowGroup.read_input(mockSpecs)

    # Checks for __init__
    #self.mockBaseInit.assert_called_once_with(testCashFlowGroup)
    self.assertEqual(testCashFlowGroup.name, "test_component")
    self.assertEqual(testCashFlowGroup._component, mockComponent)

    # Checks for read_input
    self.assertEqual(testCashFlowGroup.lifetime, 50)
    mockNewCFInstance1.read_input.assert_called_once_with(mockCFNode1)
    mockNewCFInstance2.read_input.assert_called_once_with(mockCFNode2)
    self.assertEqual(testCashFlowGroup.cashflows, [mockNewCFInstance1, mockNewCFInstance2])

    ### PART 2: XML input

    # Add and modify mocks as necessary for xml input
    mockSpecs.return_value.subparts = mockSpecs.subparts
    self.mockEconomicsParsed.return_value.parseNode.return_value = mockSpecs
    self.mockCashFlow.side_effect = [mockNewCFInstance1, mockNewCFInstance2] # Reset iterator

    mockXML = MagicMock()

    # Call the method under test with xml input
    mockGetInputSpecs = MagicMock()
    mockGetInputSpecs.return_value = mockSpecs
    with patch.object(CashFlowGroup, "get_input_specs", mockGetInputSpecs):
      testCashFlowGroup = CashFlowGroup(mockComponent) # Reset CashFlowGroup attributes
      testCashFlowGroup.read_input(mockXML, xml=True)

    # Check that xml was parsed
    mockSpecs.return_value.parseNode.assert_called_once_with(mockXML)

    # Check that specs is right by verifying that specs.subparts can be read
    self.assertEqual(testCashFlowGroup.lifetime, 50)
    self.assertEqual(testCashFlowGroup.cashflows, [mockNewCFInstance1, mockNewCFInstance2])

if __name__ == "__main__":
  unittest.main()
