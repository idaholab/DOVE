import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY

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
      call("dispatch", param_type=mockMakeEnumType.return_value, descr=ANY)
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
    self.mockParameterInputFactory.call_args_list = [] # This is crude, but it gets the job done
    self.mockSpecs.addParam.call_args_list = []

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
    self.mockParameterInputFactory.call_args_list = []
    self.mockSpecs.addParam.call_args_list = []

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
    # Note that this test also checks _set_value and 4 getter functions

    # Test-specific mock setup
    self.mockSpecs.parameterValues = {"dispatch":"independent"}
    self.mockSpecs.subparts = [self.mockCapacity, self.mockCapFactor, self.mockMinimum]

    self.mockCapacity.getName.return_value = "capacity"
    self.mockCapacity.value = 200
    self.mockCapacity.parameterValues = {"resource":"electricity"}

    self.mockCapFactor.getName.return_value = "capacity_factor"
    self.mockCapFactor.value = 0.75

    self.mockMinimum.getName.return_value = "minimum"
    self.mockMinimum.value = 50
    self.mockMinimum.parameterValues = {"resource": "electricity"}

    # Create Interaction instance and call method under test
    testInteraction = Interaction()
    testInteraction.read_input(self.mockSpecs, "testComponentName")

    # Assertions to verify behavior

    self.assertEqual(testInteraction.is_dispatchable(), "independent")
    self.assertEqual(testInteraction.get_capacity(), 150) # 200 * 0.75
    self.assertEqual(testInteraction.get_capacity_var(), "electricity")
    self.assertEqual(testInteraction.get_minimum(None), 50) # Don't care about the "meta" arg
    self.assertEqual(testInteraction._minimum_var, "electricity") # No getter for _minimum_var

    ### Test with no capacity var

    # Update mock
    self.mockCapacity.parameterValues = {}

    # Create new Interaction instance and call method under test again
    testInteractionNoCapVar = Interaction()
    testInteractionNoCapVar.read_input(self.mockSpecs, "testComponentName")

    # Check capacity var default
    self.assertEqual(testInteractionNoCapVar.get_capacity_var(), "electricity")

    ### Test with no minimum var

    # Update mocks
    self.mockCapacity.parameterValues = {"resource":"electricity"}
    self.mockMinimum.parameterValues = {}

    # Create new Interaction instance and call method under test again
    testInteractionNoMinVar = Interaction()
    testInteractionNoMinVar.read_input(self.mockSpecs, "testComponentName")

    # Check minimum var default
    self.assertEqual(testInteractionNoMinVar._minimum_var, "electricity")


if __name__ == "__main__":
  unittest.main()
