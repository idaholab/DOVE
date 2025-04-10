import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, call, patch

import numpy as np

from DOVE.src.Dispatch.PyomoModelHandler import PyomoModelHandler

class TestPyomoModelHandler(unittest.TestCase):
  # For convenience, patches and mocks that are needed for multiple tests are set up here
  def setUp(self):
    # Create patchers
    pyomoRuleLibraryPatcher = patch("DOVE.src.Dispatch.PyomoModelHandler.prl")
    pyomoStatePatcher = patch("DOVE.src.Dispatch.PyomoModelHandler.PyomoState")

    # Start patchers and store mocks
    self.mockPRL = pyomoRuleLibraryPatcher.start()
    self.mockPyomoState = pyomoStatePatcher.start()

    # Add cleanup to stop all manually started patchers
    self.addCleanup(patch.stopall)

    # Additional mocks
    self.mockCase = MagicMock(name="mockCase")
    self.mockComponent1 = MagicMock(name="mockComponent1")
    self.mockComponent2 = MagicMock(name="mockComponent2")
    self.mockInitialStorage = MagicMock(name="mockInitialStorage")
    self.mockMeta = MagicMock(name="mockMeta")

    # Helpful variables for PMH construction
    self.time = np.array([2, 4, 6, 8])
    self.time_offset = 3
    self.components = [self.mockComponent1, self.mockComponent2]
    self.resources = ["electricity", "steam"]

  def testBuildModel(self):

    # Create instance of PMH to trigger __init__, which calls build_model
    testPMH = PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.mockMeta
    )

    # Assertions to verify behavior

    # Checks for __init__
    self.assertIs(testPMH.time, self.time)
    self.assertEqual(testPMH.time_offset, self.time_offset)
    self.assertEqual(testPMH.case, self.mockCase)
    self.assertEqual(testPMH.components, self.components)
    self.assertEqual(testPMH.resources, self.resources)
    self.assertEqual(testPMH.initial_storage, self.mockInitialStorage)
    self.assertEqual(testPMH.meta, self.mockMeta)

    # Checks for build_model
    self.assertIsNotNone(testPMH.model)
    self.assertEqual(testPMH.model.C.data(), tuple([0, 1]))
    self.assertEqual(testPMH.model.R.data(), tuple([0, 1]))
    self.assertEqual(testPMH.model.T.data(), tuple([0, 1, 2, 3]))
    self.assertIs(testPMH.model.Times, self.time)
    self.assertEqual(testPMH.model.time_offset, self.time_offset)
    self.assertEqual(testPMH.model.resource_index_map, self.mockMeta["HERON"]["resource_indexer"])
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
    createConservationPatcher = patch.object(PyomoModelHandler, "_create_conservation")
    createObjectivePatcher = patch.object(PyomoModelHandler, "_create_objective")

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
      self.mockMeta
    )

    testPMH.populate_model()

    # Assertions to verify behavior

    # Check that components were processed
    expectedProcessComponentCalls = [call(self.mockComponent1), call(self.mockComponent2)]
    mockProcessComponent.assert_has_calls(expectedProcessComponentCalls)

    # Check other calls
    mockCreateConservation.assert_called_once()
    mockCreateObjective.assert_called_once()

if __name__ == "__main__":
  unittest.main()
