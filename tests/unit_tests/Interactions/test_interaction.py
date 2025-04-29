# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED

import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY

from ravenframework.utils import InputTypes

from dove.interactions import Interaction

class TestInteraction(unittest.TestCase):
  # For convenience, patches and mocks that are needed for multiple tests are set up here
  def setUp(self):
    # Create patchers
    parameterInputFactoryPatcher = patch("ravenframework.utils.InputData.parameterInputFactory")

    # Start patchers and store mocks
    self.mockParameterInputFactory = parameterInputFactoryPatcher.start()

    # Add cleanup to stop all manually started patchers
    self.addCleanup(patch.stopall)

    # Set up mocks
    self.mockSpecs = MagicMock(name="mockSpecs")
    self.mockCapacity = MagicMock(name="mockCapacity")
    self.mockCapFactor = MagicMock(name="mockCapacityFactor")
    self.mockMinimum = MagicMock(name="mockMinimum")

  def testGetInputSpecs(self):

    # Test-specific mock setup
    self.mockParameterInputFactory.side_effect = [self.mockSpecs, self.mockCapacity, self.mockCapFactor, self.mockMinimum]

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
      call("dispatch", param_type=mockMakeEnumType.return_value, required=True, descr=ANY)
    ]

    self.mockSpecs.addParam.assert_has_calls(expectedAddParamCalls)
    # Check descr is correct
    self.assertIn("produced", self.mockSpecs.addParam.call_args_list[0][1]["descr"])

    # This check is necessary because of the patch on makeEnumType
    mockMakeEnumType.assert_called_once_with("dispatch_opts", "dispatch_opts", ["fixed", "independent", "dependent"])

    # Check specs.addSub calls
    expectedAddSubCalls = [call(self.mockCapacity), call(self.mockCapFactor), call(self.mockMinimum)]
    self.mockSpecs.addSub.assert_has_calls(expectedAddSubCalls)

    # Check cap.addParam call
    self.mockCapacity.addParam.assert_called_once_with("resource", param_type=InputTypes.StringType, descr=ANY)

    # Check minn.addParam call
    self.mockMinimum.addParam.assert_called_once_with("resource", param_type=InputTypes.StringType, descr=ANY)

    # Check the returned value
    self.assertEqual(specs, self.mockSpecs)

    ### Test descriptions for storage

    # Reset mocks
    self.mockParameterInputFactory.side_effect = [self.mockSpecs, self.mockCapacity, self.mockCapFactor, self.mockMinimum]
    self.mockParameterInputFactory.reset_mock()
    self.mockSpecs.addParam.reset_mock()

    class testStorage(Interaction):
      tag = "stores"

      def __init__(self, **kwargs):
        Interaction.__init__(self, **kwargs)

    # Call the method under test again
    with patch.object(InputTypes, "makeEnumType", mockMakeEnumType):
      specs = testStorage.get_input_specs() # This is actually calling Interaction.get_input_specs

    # Assert descriptions were set correctly
    self.assertIn("stores", self.mockParameterInputFactory.call_args_list[0][1]["descr"])
    self.assertIn("stored", self.mockSpecs.addParam.call_args_list[0][1]["descr"])

    ### Test descriptions for Demand

    # Reset mocks
    self.mockParameterInputFactory.side_effect = [self.mockSpecs, self.mockCapacity, self.mockCapFactor, self.mockMinimum]
    self.mockParameterInputFactory.reset_mock()
    self.mockSpecs.addParam.reset_mock()

    class testDemand(Interaction):
      tag = "demands"

      def __init__(self, **kwargs):
        Interaction.__init__(self, **kwargs)

    # Call the method under test again
    with patch.object(InputTypes, "makeEnumType", mockMakeEnumType):
      specs = testDemand.get_input_specs() # This is actually calling Interaction.get_input_specs

    # Assert descriptions were set correctly
    self.assertIn("consumes", self.mockParameterInputFactory.call_args_list[0][1]["descr"])
    self.assertIn("consumed", self.mockSpecs.addParam.call_args_list[0][1]["descr"])

  def testReadInput(self):
    # Note that this test also checks _set_value

    # Test-specific mock setup
    self.mockSpecs.parameterValues = {"dispatch":"independent", "resource":["other_resource"]}
    self.mockSpecs.subparts = [self.mockCapacity, self.mockCapFactor, self.mockMinimum]

    self.mockCapacity.getName.return_value = "capacity"
    self.mockCapacity.value = 200
    self.mockCapacity.parameterValues = {"resource":"electricity"} # Should override resource in specs

    self.mockCapFactor.getName.return_value = "capacity_factor"
    self.mockCapFactor.value = 0.75

    self.mockMinimum.getName.return_value = "minimum"
    self.mockMinimum.value = 50
    self.mockMinimum.parameterValues = {"resource":"electricity"} # Should override resource in specs

    # Create Interaction instance and call method under test
    testInteraction = Interaction()
    testInteraction.read_input(self.mockSpecs, "testComponentName")

    # Assertions to verify behavior

    self.assertEqual(testInteraction.dispatch_flexibility, "independent")
    self.assertEqual(testInteraction._capacity_factor, 0.75)
    self.assertEqual(testInteraction.capacity_var, "electricity")
    self.assertEqual(testInteraction._capacity, 200)
    self.assertEqual(testInteraction._minimum, 50)
    self.assertEqual(testInteraction._minimum_var, "electricity")

    ### Test with no capacity or minimum var

    # Update mocks
    self.mockCapacity.parameterValues = {}
    self.mockMinimum.parameterValues = {}

    # Create new Interaction instance and call method under test again
    testInteractionMissingVars = Interaction()
    testInteractionMissingVars.read_input(self.mockSpecs, "testComponentName")

    # Check vars
    self.assertEqual(testInteractionMissingVars.capacity_var, "other_resource")
    self.assertEqual(testInteractionMissingVars._minimum_var, "other_resource")

    # NOTE: As of commit e555659, "self.capacity_var is None" (line 168 of interaction.py) will always be false
    # NOTE: As of commit e555659, "self._minimum and self._minimum_var is None" (line 175 of interaction.py) will always be false


if __name__ == "__main__":
  unittest.main()
