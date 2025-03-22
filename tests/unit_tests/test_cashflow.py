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
    # The above patcher is a workaround for an apparent bug in unittest.
    # When the patcher is not in place, the addParam.assert_has_calls line in testGetInputSpecs
    # returns a "calls not found" error, but the "actual" and "expected" calls shown are identical.

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()

    # Add cleanup to stop all manually started patchers
    self.addCleanup(patch.stopall)

  def testGetInputSpecs(self):

    # Set up mocks

    mockCashFlow = MagicMock(name="mockCashFlow")

    # Mock CashFlow subnodes, subsubnodes, etc
    mockDriver = MagicMock(name="mockDriver")
    mockReferencePrice = MagicMock(name="mockReferencePrice")
    mockLevelizedCost = MagicMock(name="mockLevelizedCost")
    mockReferenceDriver = MagicMock(name="mockReferenceDriver")
    mockScalingFactorX = MagicMock(name="mockScalingFactorX")
    mockDepreciate = MagicMock(name="mockDepreciate")

    self.mockParameterInputFactory.side_effect = [
      mockCashFlow,
      mockDriver,
      mockReferencePrice,
      mockLevelizedCost,
      mockReferenceDriver,
      mockScalingFactorX,
      mockDepreciate
    ]

    mockMakeEnumType = MagicMock(name='mockMakeEnumType')

    # Call the method under test
    # The patch below is a workaround for an apparent bug in unittest.
    # When the patch is not in place, the addParam.assert_has_calls line returns a "calls not found" error,
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

    mockCashFlow.addParam.assert_has_calls(expectedAddParamCalls)

    # This check is necessary because of the patch on makeEnumType
    expectedMakeEnumTypeCalls = [
      call("CFType", "CFType", ["one-time", "repeating"]),
      call("period_opts", "period_opts", ["hour", "year"])
    ]

    mockMakeEnumType.assert_has_calls(expectedMakeEnumTypeCalls)

    # Check cf.addSub calls
    expectedAddSubCalls = [
      call(mockDriver),
      call(mockReferencePrice),
      call(mockReferenceDriver),
      call(mockScalingFactorX),
      call(mockDepreciate)
    ]

    mockCashFlow.addSub.assert_has_calls(expectedAddSubCalls)

    # Check reference_price.addSub call
    mockReferencePrice.addSub.assert_called_with(mockLevelizedCost)

    # Check return value
    self.assertIs(specs, mockCashFlow)


if __name__ == "__main__":
  unittest.main()
