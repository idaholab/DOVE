# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED

# import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch, ANY

import numpy as np
import pyomo.environ as pyo

from dove.Dispatch import PyomoModelHandler as pmh
from dove.components import Component
from dove.interactions import Interaction, Producer, Demand, Storage

class TestPyomoModelHandler(unittest.TestCase):
  # For convenience, patches and mocks that are needed for multiple tests are set up here
  def setUp(self):
    # Create patchers
    pyomoRuleLibraryPatcher = patch("dove.Dispatch.PyomoModelHandler.prl", autospec=True)
    pyomoStatePatcher = patch("dove.Dispatch.PyomoModelHandler.PyomoState", autospec=True)

    # Start patchers and store mocks
    self.mockPRL = pyomoRuleLibraryPatcher.start()
    self.mockPyomoState = pyomoStatePatcher.start()

    # Add cleanup to stop all manually started patchers
    self.addCleanup(patch.stopall)

    # Additional mocks
    self.mockCase = MagicMock(name="mockCase")
    self.mockComponent1 = MagicMock(name="mockComponent1", spec=Component)
    self.mockComponent2 = MagicMock(name="mockComponent2", spec=Component)
    self.mockInitialStorage = MagicMock(name="mockInitialStorage")
    self.mockInteraction = MagicMock(name="mockInteraction", spec=Interaction)

    # Helpful variables for PMH construction
    self.time = np.array([2, 4, 6, 8])
    self.time_offset = 3
    self.components = [self.mockComponent1, self.mockComponent2]
    self.resources = ["electricity", "steam"]
    self.meta = {"HERON": {"resource_indexer": "resource_index_map"}} # Additional data later added if required by test

  def testBuildModel(self):

    # Create instance of PMH to trigger __init__, which calls build_model
    testPMH = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Assertions to verify behavior

    # Checks for __init__
    self.assertIs(testPMH.time, self.time)
    self.assertEqual(testPMH.time_offset, self.time_offset)
    # self.assertEqual(testPMH.case, self.mockCase)
    self.assertEqual(testPMH.components, self.components)
    self.assertEqual(testPMH.resources, self.resources)
    self.assertEqual(testPMH.initial_storage, self.mockInitialStorage)
    self.assertEqual(testPMH.meta, self.meta)

    # Checks for build_model
    self.assertIsNotNone(testPMH.model)
    self.assertEqual(testPMH.model.C.data(), tuple([0, 1]))
    self.assertEqual(testPMH.model.R.data(), tuple([0, 1]))
    self.assertEqual(testPMH.model.T.data(), tuple([0, 1, 2, 3]))
    self.assertIs(testPMH.model.Times, self.time)
    self.assertEqual(testPMH.model.time_offset, self.time_offset)
    self.assertEqual(testPMH.model.resource_index_map, "resource_index_map")
    # self.assertEqual(testPMH.model.Case, self.mockCase)
    self.assertEqual(testPMH.model.Components, self.components)

    # Check that model activity was initialized correctly
    self.assertEqual(testPMH.model.Activity, self.mockPyomoState.return_value)
    self.mockPyomoState.return_value.initialize.assert_called_once_with(
      testPMH.model.Components, testPMH.model.resource_index_map, testPMH.model.Times, testPMH.model
    )

  ### THE BELOW TESTS ASSUME THAT BUILD_MODEL AND __INIT__ FUNCTION PROPERLY ###

  def testPopulateModel(self):

    # Set up test-specific patchers
    processComponentPatcher = patch.object(pmh.PyomoModelHandler, "_process_component")
    createConservationPatcher = patch.object(pmh.PyomoModelHandler, "_create_conservation", autospec=True)
    createObjectivePatcher = patch.object(pmh.PyomoModelHandler, "_create_objective", autospec=True)

    # Start test-specific patchers and store mocks
    mockProcessComponent = processComponentPatcher.start()
    mockCreateConservation = createConservationPatcher.start()
    mockCreateObjective = createObjectivePatcher.start()

    # Create PMH instance and call method under test
    testPMH = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    testPMH.populate_model()

    # Assertions to verify behavior

    # Check that components were processed
    expectedProcessComponentCalls = [call(self.mockComponent1), call(self.mockComponent2)]
    mockProcessComponent.assert_has_calls(expectedProcessComponentCalls)

    # Check other calls
    mockCreateConservation.assert_called_once()
    mockCreateObjective.assert_called_once()

  def testProcessComponent(self):

    # Set up test-specific patchers
    processGovernedComponentPatcher = patch.object(pmh.PyomoModelHandler, "_process_governed_component")
    createStoragePatcher = patch.object(pmh.PyomoModelHandler, "_create_storage")
    createProductionPatcher = patch.object(pmh.PyomoModelHandler, "_create_production")

    # Start test-specific patchers and store mocks
    mockProcessGovernedComponent = processGovernedComponentPatcher.start()
    mockCreateStorage = createStoragePatcher.start()
    mockCreateProduction = createProductionPatcher.start()

    # Create PMH instance
    testPMH = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    ### With governed storage

    # Configure mocks
    self.mockComponent1.interaction.is_governed.return_value = True
    self.mockComponent1.interaction.mock_add_spec(Storage)

    # Call method under test
    testPMH._process_component(self.mockComponent1)

    # Check that only correct function called
    mockProcessGovernedComponent.assert_called_once_with(self.mockComponent1)
    mockCreateStorage.assert_not_called()
    mockCreateProduction.assert_not_called()

    ### With non-governed storage

    # Configure mocks
    self.mockComponent1.interaction.is_governed.return_value = False
    # Still has Storage spec, so don't need to add it

    mockProcessGovernedComponent.reset_mock()

    # Call method under test
    testPMH._process_component(self.mockComponent1)

    # Check that only correct function called
    mockProcessGovernedComponent.assert_not_called()
    mockCreateStorage.assert_called_once_with(self.mockComponent1)
    mockCreateProduction.assert_not_called()

    ### With producer

    # Configure mocks
    self.mockComponent1.interaction.is_governed.return_value = False
    self.mockComponent1.interaction.mock_add_spec(Producer)

    mockCreateStorage.reset_mock()

    # Call method under test
    testPMH._process_component(self.mockComponent1)

    # Check that only correct function called
    mockProcessGovernedComponent.assert_not_called()
    mockCreateStorage.assert_not_called()
    mockCreateProduction.assert_called_once_with(self.mockComponent1)


  def testProcessGovernedComponent(self):

    # Set up test-specific patchers
    processStorageComponentPatcher = patch.object(pmh.PyomoModelHandler, "_process_storage_component")
    createProductionParamPatcher = patch.object(pmh.PyomoModelHandler, "_create_production_param")

    # Start test-specific patchers and store mocks
    mockProcessStorageComponent = processStorageComponentPatcher.start()
    mockCreateProductionParam = createProductionParamPatcher.start()

    # Set up activity value
    self.mockComponent1.interaction.get_strategy.return_value.evaluate.return_value = [{"level": "expected_activity_value"}]

    # Create PMH instance
    testPMH = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    ### With storage

    # Configure mocks
    self.mockComponent1.interaction.mock_add_spec(Storage)

    # Call method under test
    testPMH._process_governed_component(self.mockComponent1)

    # Check meta
    self.assertEqual(testPMH.meta["request"]["component"], self.mockComponent1)
    self.assertIs(testPMH.meta["request"]["time"], self.time)

    # Check that only correct function called
    mockProcessStorageComponent.assert_called_once_with(self.mockComponent1)
    mockCreateProductionParam.assert_not_called()

    ### With production param

    # Configure mocks
    # FIXME: The below line causes an error because get_strategy (mentioned in line 203 above) is only in Storage.
    #        But if it was a Storage, then process_storage_component should have been called.
    #        Is the else block supposed to be runnable?
    self.mockComponent1.interaction.mock_add_spec(Producer)
    mockProcessStorageComponent.reset_mock()

    # Call method under test
    testPMH._process_governed_component(self.mockComponent1)

    # Check activity call
    self.mockComponent1.interaction.get_strategy.return_value.evaluate.assert_called_once_with(self.meta)

    # Check that only correct function called
    mockProcessStorageComponent.assert_not_called()
    mockCreateProductionParam.assert_called_once_with(self.mockComponent1, "expected_activity_value")

  def testProcessStorageComponent(self):

    # Set up test-specific patchers
    createProductionParamPatcher = patch.object(pmh.PyomoModelHandler, "_create_production_param")

    # Start test-specific patchers and store mocks
    mockCreateProductionParam = createProductionParamPatcher.start()

    # Configure additional mocks
    self.mockComponent1.interaction.mock_add_spec(Storage)
    activity = [0, 1, 3, 1]
    self.mockComponent1.interaction.get_strategy.return_value.evaluate.return_value = [{"level": activity}]
    # FIXME: The following line causes an error because Storage doesn't have a get_initial_level method
    self.mockComponent1.interaction.get_initial_level.return_value = 1

    self.mockComponent1.interaction.sqrt_rte = 0.5

    # Create PMH instance
    testPMH = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Call method under test
    testPMH._process_storage_component(self.mockComponent1)

    # Check interaction calls
    self.mockComponent1.interaction.get_strategy.return_value.evaluate.assert_called_once_with(self.meta)
    self.mockComponent1.get_initial_level.assert_called_once_with(self.meta)

    # Check CreateProductionParam calls
    # Equality checks don't work on entire numpy arrays, so we have to go through the calls manually

    levelCallFound = False
    chargeCallFound = False
    dischargeCallFound = False

    expectedCharge = np.array([0, -1, -2, 0])
    expectedDischarge = np.array([0.25, 0, 0, 0.5])

    expectedLevelCall = call(self.mockComponent1, activity, tag="level")
    expectedChargeCall = call(self.mockComponent1, expectedCharge, tag="charge")
    expectedDischargeCall = call(self.mockComponent1, expectedDischarge, tag="discharge")

    # The equality operator returns an array of booleans; .all() checks that all elements are true
    # Format: Call list -> specific call -> args/kwargs -> specific arg/kwarg
    for cppCall in mockCreateProductionParam.call_args_list:
      if cppCall[0][0] is self.mockComponent1 and cppCall[0][1] is activity and cppCall[1]["tag"] == "level":
        levelCallFound = True
      elif cppCall[0][0] is self.mockComponent1 and (cppCall[0][1] == expectedCharge).all() and cppCall[1]["tag"] == "charge":
        chargeCallFound = True
      elif cppCall[0][0] is self.mockComponent1 and (cppCall[0][1] == expectedDischarge).all() and cppCall[1]["tag"] == "discharge":
        dischargeCallFound = True
      else:
        message =   "Unexpected call to PyomoModelHandler._create_production_param.\n"
        expected = f"Expected: {[expectedLevelCall, expectedChargeCall, expectedDischargeCall]}\n"
        actual =   f"  Actual: {cppCall}"
        raise AssertionError(message + expected + actual)

    if not levelCallFound:
      message =   "Expected call to PyomoModelHandler._create_production_param not found.\n"
      expected = f"Expected: {expectedLevelCall}\n"
      actual =   f"  Actual: {mockCreateProductionParam.call_args_list}"
      raise AssertionError(message + expected + actual)

    if not chargeCallFound:
      message =   "Expected call to PyomoModelHandler._create_production_param not found.\n"
      expected = f"Expected: {expectedChargeCall}\n"
      actual =   f"  Actual: {mockCreateProductionParam.call_args_list}"
      raise AssertionError(message + expected + actual)

    if not dischargeCallFound:
      message =   "Expected call to PyomoModelHandler._create_production_param not found.\n"
      expected = f"Expected: {expectedDischargeCall}\n"
      actual =   f"  Actual: {mockCreateProductionParam.call_args_list}"
      raise AssertionError(message + expected + actual)

  def testCreateProductionLimit(self):

    # Configure mocks
    def fake_prod_limit_rule(prod_name, r, limits, kind, t, m):
      return pyo.Constraint.Feasible

    mockFakeProdLimitRule = MagicMock(name="mockFakeProdLimitRule", wraps=fake_prod_limit_rule) # To track calls
    self.mockPRL.prod_limit_rule = mockFakeProdLimitRule

    mockConstraint = MagicMock(name="mockConstraint")
    mockConstraint.Feasible = pyo.Constraint.Feasible # For fake rule
    mockConstraint.return_value = "fake_constr"

    # Add patcher to track calls to pyo.Constraint and control return value
    constraintPatcher = patch.object(pmh.pyo, "Constraint", mockConstraint)
    constraintPatcher.start()

    # Modify arguments for constructor
    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 1}}
    self.mockComponent1.name = "comp1_name"

    # Create PMH instance
    testPMH = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Set up validation dict for input to method under test
    validation = {
      "component": self.mockComponent1,
      "resource": "electricity",
      "time_index": 2,
      "limit": 3,
      "limit_type": "upper"
    }

    # Call method under test
    testPMH._create_production_limit(validation)

    # Check that constraint was created from rule
    rule = mockConstraint.call_args[1]["rule"]
    # Checks that the rule added is a lambda function
    self.assertEqual(rule.__name__, "<lambda>")

    # Check that rule was set up correctly
    rule("fake_mod") # Call the lambda function so we can read the other call args off the mock
    mockFakeProdLimitRule.assert_called_once_with("comp1_name_production", 1, ANY, "upper", 2, "fake_mod")
    # Have to check limits arg explicitly since it's a numpy array
    self.assertTrue((mockFakeProdLimitRule.call_args[0][2] == np.array([0, 0, 3, 0])).all()) # All elements are the same

    # Check that constraint was added to model correctly
    self.assertIs(testPMH.model.comp1_name_electricity_2_vld_limit_constr_1, "fake_constr")


if __name__ == "__main__":
  unittest.main()
