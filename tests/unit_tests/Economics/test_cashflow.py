import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY

from ravenframework.utils import InputData, InputTypes

from DOVE.src.Economics import CashFlow

class TestCashFlow(unittest.TestCase):
  # For convenience, patches and mocks that are needed for multiple tests are set up here
  def setUp(self):
    # Create patchers
    parameterInputFactoryPatcher = patch("ravenframework.utils.InputData.parameterInputFactory")

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()

    # Add cleanup to stop all manually started patchers
    self.addCleanup(patch.stopall)

    # Set up mocks

    self.mockCashFlow = MagicMock(name="mockCashFlow")

    # Mock CashFlow subnodes, subsubnodes, etc
    self.mockDriver = MagicMock(name="mockDriver")
    self.mockReferencePrice = MagicMock(name="mockReferencePrice")
    self.mockLevelizedCost = MagicMock(name="mockLevelizedCost")
    self.mockReferenceDriver = MagicMock(name="mockReferenceDriver")
    self.mockScalingFactorX = MagicMock(name="mockScalingFactorX")
    self.mockDepreciate = MagicMock(name="mockDepreciate")

  def testGetInputSpecs(self):

    self.mockParameterInputFactory.side_effect = [
      self.mockCashFlow,
      self.mockDriver,
      self.mockReferencePrice,
      self.mockLevelizedCost,
      self.mockReferenceDriver,
      self.mockScalingFactorX,
      self.mockDepreciate
    ]

    mockMakeEnumType = MagicMock(name='mockMakeEnumType')

    # Call the method under test
    # The patch below is a workaround for an apparent bug in unittest.
    # When the patch is not in place, the addParam.assert_has_calls line returns a "calls not found" failure,
    # but the "actual" and "expected" calls shown are identical.
    with patch.object(InputTypes, "makeEnumType", mockMakeEnumType):
      specs = CashFlow.get_input_specs()

    # Assertions to verify behavior

    # Check parameterInputFactory calls
    expectedParameterInputFactoryCalls = [
      call("CashFlow", descr=ANY),
      call("driver", contentType=InputTypes.FloatOrIntType, descr=ANY),
      call("reference_price", contentType=InputTypes.FloatOrIntType, descr=ANY),
      call("levelized_cost", strictMode=True, descr=ANY),
      call("reference_driver", contentType=InputTypes.FloatOrIntType, descr=ANY),
      call("scaling_factor_x", contentType=InputTypes.FloatType, descr=ANY),
      call("depreciate", contentType=InputTypes.IntegerType, descr=ANY)
    ]

    self.mockParameterInputFactory.assert_has_calls(expectedParameterInputFactoryCalls)

    # Check cf.addParam calls
    expectedAddParamCalls = [
      call("name", param_type=InputTypes.StringType, required=True, descr=ANY),
      call("type", param_type=mockMakeEnumType.return_value, required=True, descr=ANY),
      call("taxable", param_type=InputTypes.BoolType, required=True, descr=ANY),
      call("inflation", param_type=InputTypes.StringType, required=True, descr=ANY),
      call("mult_target", param_type=InputTypes.BoolType, required=False, descr=ANY),
      call("npv_exempt", param_type=InputTypes.BoolType, required=False, default=False, descr=ANY),
      call("period", param_type=mockMakeEnumType.return_value, required=False, descr=ANY)
    ]

    self.mockCashFlow.addParam.assert_has_calls(expectedAddParamCalls)

    # This check is necessary because of the patch on makeEnumType
    expectedMakeEnumTypeCalls = [
      call("CFType", "CFType", ["one-time", "repeating"]),
      call("period_opts", "period_opts", ["hour", "year"])
    ]

    mockMakeEnumType.assert_has_calls(expectedMakeEnumTypeCalls)

    # Check cf.addSub calls
    expectedAddSubCalls = [
      call(self.mockDriver),
      call(self.mockReferencePrice),
      call(self.mockReferenceDriver),
      call(self.mockScalingFactorX),
      call(self.mockDepreciate)
    ]

    self.mockCashFlow.addSub.assert_has_calls(expectedAddSubCalls)

    # Check reference_price.addSub call
    self.mockReferencePrice.addSub.assert_called_with(self.mockLevelizedCost)

    # Check return value
    self.assertIs(specs, self.mockCashFlow)

  def testReadInput(self):
    # Note that this test also checks __init__(mostly), _set_value, and 11 getter functions

    # Set up mocks
    mockComponent = MagicMock(name="mockComponent")

    self.mockCashFlow.parameterValues = {
      "name": "testCashFlowName",
      "taxable": False,
      "inflation": False,
      "type": "one-time",
      "period": "yearly",
      "npv_exempt": True
    }

    self.mockCashFlow.subparts = [
      self.mockDriver,
      self.mockReferencePrice,
      self.mockReferenceDriver,
      self.mockScalingFactorX,
      self.mockDepreciate
    ]

    self.mockDriver.getName.return_value = "driver"
    self.mockReferencePrice.getName.return_value = "reference_price"
    self.mockReferenceDriver.getName.return_value = "reference_driver"
    self.mockScalingFactorX.getName.return_value = "scaling_factor_x"
    self.mockDepreciate.getName.return_value = "depreciate"

    mockSetReferencePrice = MagicMock(name="mockSetReferencePrice")
    mockSetReferencePrice.return_value = False

    # Create CashFlow instance and call method under test
    with patch.object(CashFlow, "set_reference_price", mockSetReferencePrice):
      testCashFlow = CashFlow(mockComponent)
      testCashFlow.read_input(self.mockCashFlow)

    # Assertions to verify behavior

    # Check component assignment in __init__
    self.assertEqual(testCashFlow._component, mockComponent)

    # Check param values
    self.assertEqual(testCashFlow.name, "testCashFlowName")
    self.assertEqual(testCashFlow.is_taxable(), False)
    self.assertEqual(testCashFlow.is_inflation(), False)
    self.assertEqual(testCashFlow.get_type(), "one-time")
    self.assertEqual(testCashFlow.get_period(), "yearly")
    self.assertEqual(testCashFlow.is_npv_exempt(), True)

    self.assertEqual(testCashFlow.get_driver(), self.mockDriver.value)
    self.assertEqual(testCashFlow.get_reference(), self.mockReferenceDriver.value)
    self.assertEqual(testCashFlow.get_scale(), self.mockScalingFactorX.value)
    # self.assertEqual(testCashFlow.get_price(), 1)
    self.assertEqual(testCashFlow.get_depreciation(), self.mockDepreciate.value)

    # Check correct call to set_reference_price
    mockSetReferencePrice.assert_called_once_with(self.mockReferencePrice)
    self.assertEqual(testCashFlow.is_mult_target(), False)

    # Test that default attribute values work properly

    # Remove attributes with defaults from mock
    del self.mockCashFlow.parameterValues["period"]
    del self.mockCashFlow.parameterValues["npv_exempt"]

    # Create another CashFlow instance and call method under test
    testCashFlowDefaults = CashFlow(mockComponent)
    with patch.object(CashFlow, "set_reference_price", mockSetReferencePrice):
      testCashFlowDefaults.read_input(self.mockCashFlow)

    # Check that defaults were added correctly
    self.assertEqual(testCashFlowDefaults.get_period(), "hour")
    self.assertEqual(testCashFlowDefaults.is_npv_exempt(), False)

    # Test that method returns error with bad subnode

    # Create mock and add to subparts
    mockBadSub = MagicMock(name="mockBadSub")
    mockBadSub.get_name.return_value = "unrecognized_name"
    self.mockCashFlow.subparts.append(mockBadSub)

    # Create another CashFlow instance and call method under test again
    testCashFlowBadSubnode = CashFlow(mockComponent)
    with patch.object(CashFlow, "set_reference_price", mockSetReferencePrice):
      with self.assertRaises(IOError):
        testCashFlowBadSubnode.read_input(self.mockCashFlow)

    # Test that method returns error with no driver

    # Remove driver from subparts in mock
    self.mockCashFlow.subparts = [
      self.mockReferencePrice,
      self.mockReferenceDriver,
      self.mockScalingFactorX,
      self.mockDepreciate
    ]

    # Create another CashFlow instance and call method under test again
    testCashFlowNoDriver = CashFlow(mockComponent)
    with patch.object(CashFlow, "set_reference_price", mockSetReferencePrice):
      with self.assertRaises(IOError):
        testCashFlowNoDriver.read_input(self.mockCashFlow)

    ######## TODO ########
    # Add checks/tests for _alpha, set_reference_price, and related code


if __name__ == "__main__":
  unittest.main()
