import __init__  # Running __init__ here enables importing from DOVE and RAVEN

import unittest
from unittest.mock import MagicMock, patch

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

  def testBuildModel(self):

    time = np.array([2, 4, 6, 8])
    time_offset = 3
    components = [self.mockComponent1, self.mockComponent2]
    resources = ["electricity", "steam"]

    # Create instance of PMH to trigger __init__, which calls build_model
    testPMH = PyomoModelHandler(
      time, time_offset, self.mockCase, components, resources, self.mockInitialStorage, self.mockMeta
    )

    # Assertions to verify behavior

    # Checks for __init__
    self.assertIs(testPMH.time, time)
    self.assertEqual(testPMH.time_offset, time_offset)
    self.assertEqual(testPMH.case, self.mockCase)
    self.assertEqual(testPMH.components, components)
    self.assertEqual(testPMH.resources, resources)
    self.assertEqual(testPMH.initial_storage, self.mockInitialStorage)
    self.assertEqual(testPMH.meta, self.mockMeta)

    # Checks for build_model
    self.assertIsNotNone(testPMH.model)
    self.assertEqual(testPMH.model.C.data(), tuple([0, 1]))
    self.assertEqual(testPMH.model.R.data(), tuple([0, 1]))
    self.assertEqual(testPMH.model.T.data(), tuple([0, 1, 2, 3]))
    self.assertIs(testPMH.model.Times, time)
    self.assertEqual(testPMH.model.time_offset, time_offset)
    self.assertEqual(testPMH.model.resource_index_map, self.mockMeta["HERON"]["resource_indexer"])
    self.assertEqual(testPMH.model.Case, self.mockCase)
    self.assertEqual(testPMH.model.Components, components)


    # Check that model activity was initialized correctly
    self.assertEqual(testPMH.model.Activity, self.mockPyomoState.return_value)
    self.mockPyomoState.return_value.initialize.assert_called_once_with(
      testPMH.model.Components, testPMH.model.resource_index_map, testPMH.model.Times, testPMH.model
    )

if __name__ == "__main__":
  unittest.main()
