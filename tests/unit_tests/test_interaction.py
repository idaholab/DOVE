import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY
import re

from ravenframework.utils import InputData, InputTypes

from DOVE.src.Interactions import Interaction

class TestInteraction(unittest.TestCase):
  # For convenience, patches and mocks that are needed for multiple tests are set up here
  def setUp(self):
    # Create patchers
    parameterInputFactoryPatcher = patch("ravenframework.utils.InputData.parameterInputFactory")

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()

    # Add cleanup to stop all manually started patchers
    self.addCleanup(patch.stopall)

  def testGetInputSpecs(self):

    # Set up test-specific mocks
    mockSpecs = MagicMock(name="mockSpecs")
    mockCapacity = MagicMock(name="mockCapacity")
    mockCapFactor = MagicMock(name="mockCapacityFactor")
    mockMinimum = MagicMock(name="mockMinimum")

    self.mockParameterInputFactory.side_effect = [mockSpecs, mockCapacity, mockCapFactor, mockMinimum]

    mockMakeEnumType = MagicMock(name="mockMakeEnumType")

    class testProducer(Interaction):
      tag = "produces"

      def __init__(self, **kwargs):
        Interaction.__init__(self, **kwargs)

    # Call the method under test
    with patch.object(InputTypes, "makeEnumType", mockMakeEnumType):
      # The patch below is a workaround for an apparent bug in unittest.
      # When the patch is not in place, the addParam.assert_has_calls line returns a "calls not found" failure,
      # but the "actual" and "expected" calls shown are identical.
      specs = testProducer.get_input_specs() # This is actually calling Interaction.get_input_specs

    # Assertions to verify behavior

    expectedParameterInputFactoryCalls = [
      call("produces", ordered=False, descr=ANY), # Also want to know if descr is right (see below)
      call("capacity", contentType=InputTypes.FloatOrIntType, descr=ANY),
      call("capacity_factor", contentType=InputTypes.FloatOrIntType, descr=ANY),
      call("minimum", contentType=InputTypes.FloatOrIntType, descr=ANY)
    ]

    self.mockParameterInputFactory.assert_has_calls(expectedParameterInputFactoryCalls)
    # Check descr is correct
    # Assert first call to the factory -> kwargs -> "descr" includes str "produces"
    self.assertIn("produces", self.mockParameterInputFactory.call_args_list[0][1]["descr"])

    # Check specs.addParam calls
    expectedAddParamCalls = [
      call("resource", param_type=InputTypes.StringListType, required=True, descr=ANY), # Check descr below
      call("dispatch", param_type=mockMakeEnumType.return_value, descr=ANY)
    ]

    mockSpecs.addParam.assert_has_calls(expectedAddParamCalls)
    # Check descr is correct
    self.assertIn("produced", mockSpecs.addParam.call_args_list[0][1]["descr"])

    # This check is necessary because of the patch on makeEnumType
    mockMakeEnumType.assert_called_once_with("dispatch_opts", "dispatch_opts", ["fixed", "independent", "dependent"])

    # Check specs.addSub calls
    expectedAddSubCalls = [call(mockCapacity), call(mockCapFactor), call(mockMinimum)]
    mockSpecs.addSub.assert_has_calls(expectedAddSubCalls)

    # Check cap.addParam call
    mockCapacity.addParam.assert_called_once_with("resource", param_type=InputTypes.StringType, descr=ANY)

    # Check minn.addParam call
    mockMinimum.addParam.assert_called_once_with("resource", param_type=InputTypes.StringType, descr=ANY)

    # Check the returned value
    self.assertEqual(specs, mockSpecs)

    ### Test descriptions for storage

    # Reset mocks
    self.mockParameterInputFactory.side_effect = [mockSpecs, mockCapacity, mockCapFactor, mockMinimum]
    self.mockParameterInputFactory.call_args_list = [] # This is crude, but it gets the job done
    mockSpecs.addParam.call_args_list = []

    class testStorage(Interaction):
      tag = "stores"

      def __init__(self, **kwargs):
        Interaction.__init__(self, **kwargs)

    # Call the method under test again
    with patch.object(InputTypes, "makeEnumType", mockMakeEnumType):
      specs = testStorage.get_input_specs() # This is actually calling Interaction.get_input_specs

    # Assert descriptions were set correctly
    self.assertIn("stores", self.mockParameterInputFactory.call_args_list[0][1]["descr"])
    self.assertIn("stored", mockSpecs.addParam.call_args_list[0][1]["descr"])

    ### Test descriptions for Demand

    # Reset mocks
    self.mockParameterInputFactory.side_effect = [mockSpecs, mockCapacity, mockCapFactor, mockMinimum]
    self.mockParameterInputFactory.call_args_list = []
    mockSpecs.addParam.call_args_list = []

    class testDemand(Interaction):
      tag = "demands"

      def __init__(self, **kwargs):
        Interaction.__init__(self, **kwargs)

    # Call the method under test again
    with patch.object(InputTypes, "makeEnumType", mockMakeEnumType):
      specs = testDemand.get_input_specs() # This is actually calling Interaction.get_input_specs

    # Assert descriptions were set correctly
    self.assertIn("consumes", self.mockParameterInputFactory.call_args_list[0][1]["descr"])
    self.assertIn("consumed", mockSpecs.addParam.call_args_list[0][1]["descr"])


if __name__ == "__main__":
  unittest.main()
