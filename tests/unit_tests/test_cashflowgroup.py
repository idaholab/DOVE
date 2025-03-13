import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY

from ravenframework.utils import InputData, InputTypes

from DOVE.src.Economics import CashFlowGroup

class TestCashFlowGroup(unittest.TestCase):
  # For convenience, patches and mocks that are needed for all tests are set up here
  def setUp(self):
    # Create patchers
    parameterInputFactoryPatcher = patch("ravenframework.utils.InputData.parameterInputFactory")
    cashFlowPatcher = patch("DOVE.src.Economics.CashFlowGroup.CashFlow")

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()
    self.mockCashFlow = cashFlowPatcher.start()

    # Add cleanup to stop manually started patchers
    self.addCleanup(patch.stopall)

  def testGetInputSpecs(self):

    mockEconomicsParameterInput = MagicMock()
    mockLifetimeParameterInput = MagicMock()
    self.mockParameterInputFactory.side_effect = [mockEconomicsParameterInput, mockLifetimeParameterInput]

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
      call(mockLifetimeParameterInput),
      call(self.mockCashFlow.get_input_specs())
    ]

    mockEconomicsParameterInput.addSub.assert_has_calls(expectedAddSubCalls)

    # Check the returned value
    self.assertEqual(specs, mockEconomicsParameterInput)


if __name__ == "__main__":
  unittest.main()
