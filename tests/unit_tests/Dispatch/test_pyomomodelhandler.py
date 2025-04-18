import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch

import numpy as np

from DOVE.src.Dispatch.PyomoModelHandler import PyomoModelHandler
from DOVE.src.Components import Component
from DOVE.src.Interactions import Interaction

class TestPyomoModelHandler(unittest.TestCase):
  # For convenience, patches and mocks that are needed for multiple tests are set up here
  def setUp(self):
    # Create patchers
    pyomoRuleLibraryPatcher = patch("DOVE.src.Dispatch.PyomoModelHandler.prl", autospec=True)
    pyomoStatePatcher = patch("DOVE.src.Dispatch.PyomoModelHandler.PyomoState", autospec=True)

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
    testPMH = PyomoModelHandler(
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
    self.assertEqual(testPMH.case, self.mockCase)
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
    self.assertEqual(testPMH.model.Case, self.mockCase)
    self.assertEqual(testPMH.model.Components, self.components)


    # Check that model activity was initialized correctly
    self.assertEqual(testPMH.model.Activity, self.mockPyomoState.return_value)
    self.mockPyomoState.return_value.initialize.assert_called_once_with(
      testPMH.model.Components, testPMH.model.resource_index_map, testPMH.model.Times, testPMH.model
    )

  ### THE BELOW TESTS ASSUME THAT BUILD_MODEL AND __INIT__ FUNCTION PROPERLY ###

  def testPopulateModel(self):

    # Set up test-specific patchers
    processComponentPatcher = patch.object(PyomoModelHandler, "_process_component")
    createConservationPatcher = patch.object(PyomoModelHandler, "_create_conservation", autospec=True)
    createObjectivePatcher = patch.object(PyomoModelHandler, "_create_objective", autospec=True)

    # Start test-specific patchers and store mocks
    mockProcessComponent = processComponentPatcher.start()
    mockCreateConservation = createConservationPatcher.start()
    mockCreateObjective = createObjectivePatcher.start()

    # Create PMH instance and call method under test
    testPMH = PyomoModelHandler(
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
    processGovernedComponentPatcher = patch.object(PyomoModelHandler, "_process_governed_component")
    createStoragePatcher = patch.object(PyomoModelHandler, "_create_storage")
    createProductionPatcher = patch.object(PyomoModelHandler, "_create_production")

    # Start test-specific patchers and store mocks
    mockProcessGovernedComponent = processGovernedComponentPatcher.start()
    mockCreateStorage = createStoragePatcher.start()
    mockCreateProduction = createProductionPatcher.start()

    # Additional mock configuration
    self.mockComponent1.get_interaction.return_value = self.mockInteraction

    # Create PMH instance
    testPMH = PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    ### With governed component

    # Configure mock interaction
    self.mockInteraction.is_governed.return_value = True

    # Call method under test
    testPMH._process_component(self.mockComponent1)

    # Check that only correct function called
    mockProcessGovernedComponent.assert_called_once_with(self.mockComponent1, self.mockInteraction)
    mockCreateStorage.assert_not_called()
    mockCreateProduction.assert_not_called()

    ### With storage

    # Configure mocks
    self.mockInteraction.is_governed.return_value = False
    self.mockInteraction.is_type.return_value = True

    mockProcessGovernedComponent.reset_mock()

    # Call method under test
    testPMH._process_component(self.mockComponent1)

    # Check type
    self.mockInteraction.is_type.assert_called_once_with("HeronStorage")

    # Check that only correct function called
    mockProcessGovernedComponent.assert_not_called()
    mockCreateStorage.assert_called_once_with(self.mockComponent1)
    mockCreateProduction.assert_not_called()

    ### With production

    # Configure mocks
    self.mockInteraction.is_type.return_value = False

    mockCreateStorage.reset_mock()

    # Call method under test
    testPMH._process_component(self.mockComponent1)

    # Check that only correct function called
    mockProcessGovernedComponent.assert_not_called()
    mockCreateStorage.assert_not_called()
    mockCreateProduction.assert_called_once_with(self.mockComponent1)


  def testProcessGovernedComponent(self):

    # Set up test-specific patchers
    processStorageComponentPatcher = patch.object(PyomoModelHandler, "_process_storage_component")
    createProductionParamPatcher = patch.object(PyomoModelHandler, "_create_production_param")

    # Start test-specific patchers and store mocks
    mockProcessStorageComponent = processStorageComponentPatcher.start()
    mockCreateProductionParam = createProductionParamPatcher.start()

    # Set up activity value
    # FIXME: Uncomment the below line once get_strategy bug is fixed
    # self.mockInteraction.get_strategy.return_value.evaluate.return_value = [{"level": "expected_activity_value"}]

    # Create PMH instance
    testPMH = PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    ### With storage

    # Configure mock interaction
    self.mockInteraction.is_type.return_value = True

    # Call method under test
    testPMH._process_governed_component(self.mockComponent1, self.mockInteraction)

    # Check meta and type
    self.assertEqual(testPMH.meta["request"]["component"], self.mockComponent1)
    self.assertIs(testPMH.meta["request"]["time"], self.time)
    self.mockInteraction.is_type.assert_called_once_with("HeronStorage")

    # Check that only correct function called
    mockProcessStorageComponent.assert_called_once_with(self.mockComponent1, self.mockInteraction)
    mockCreateProductionParam.assert_not_called()

    ### With production param

    # Configure mocks
    self.mockInteraction.is_type.return_value = False
    mockProcessStorageComponent.reset_mock()

    # Call method under test
    testPMH._process_governed_component(self.mockComponent1, self.mockInteraction)

    # Check activity call
    self.mockInteraction.get_strategy.return_value.evaluate.assert_called_once_with(self.meta)

    # Check that only correct function called
    mockProcessStorageComponent.assert_not_called()
    mockCreateProductionParam.assert_called_once_with(self.mockComponent1, "expected_activity_value")


if __name__ == "__main__":
  unittest.main()
