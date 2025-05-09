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
from dove.physics import Ratio, Polynomial

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
    self.mockComponent1.name = "comp1"
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

    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For fake rule
    mockPyoConstraint.return_value = "fake_constr"

    # Add patcher to track calls to pyo.Constraint and control return value
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)
    pyoConstraintPatcher.start()

    # Modify meta
    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 1}}

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
    rule = mockPyoConstraint.call_args[1]["rule"]
    # Checks that the rule added is a lambda function
    self.assertEqual(rule.__name__, "<lambda>")

    # Check that rule was set up correctly
    rule("fake_mod") # Call the lambda function so we can read the other call args off the mock
    mockFakeProdLimitRule.assert_called_once_with("comp1_production", 1, ANY, "upper", 2, "fake_mod")
    # Have to check limits arg explicitly since it's a numpy array
    self.assertTrue((mockFakeProdLimitRule.call_args[0][2] == np.array([0, 0, 3, 0])).all()) # All elements are the same

    # Check that constraint was added to model correctly
    self.assertIs(testPMH.model.comp1_electricity_2_vld_limit_constr_1, "fake_constr")

  def testCreateProductionParam(self):

    # Set up and start test-specific patchers
    paramPatcher = patch.object(pmh.pyo, "Param")
    mockParam = paramPatcher.start()

    # Set up other inputs for constructor and test method
    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 0, "h2": 1}}
    values = np.array([0, -1, -2, 0])

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
    testPMH._create_production_param(self.mockComponent1, values)

    # Check that resource indexer was set correctly
    resource_indexer = testPMH.model.comp1_res_index_map
    self.assertSetEqual(resource_indexer, set([0, 1]))

    # Check that production param was created and set correctly
    init_dict = {(0, 0): 0, (0, 1): -1, (0, 2): -2, (0, 3): 0}
    mockParam.assert_called_once_with(resource_indexer, set([0, 1, 2, 3]), initialize=init_dict)

    self.assertEqual(testPMH.model.comp1_production, mockParam.return_value)

  def testCreateProduction(self):

    # Set up test-specific patchers
    createProductionVariablePatcher = patch.object(pmh.PyomoModelHandler, "_create_production_variable")
    createTransferPatcher = patch.object(pmh.PyomoModelHandler, "_create_transfer")
    createRampLimitPatcher = patch.object(pmh.PyomoModelHandler, "_create_ramp_limit")

    # Start test-specific patchers and store mocks
    mockCreateProductionVariable = createProductionVariablePatcher.start()
    mockCreateTransfer = createTransferPatcher.start()
    mockRampLimit = createRampLimitPatcher.start()

    # Configure mocks
    mockCreateProductionVariable.return_value = "comp1_prod"
    self.mockComponent1.interaction.mock_add_spec(Producer)

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
    returned = testPMH._create_production(self.mockComponent1)

    # Check mock calls
    mockCreateProductionVariable.assert_called_once_with(self.mockComponent1)
    mockCreateTransfer.assert_called_once_with(self.mockComponent1, "comp1_prod")
    mockRampLimit.assert_called_once_with(self.mockComponent1, "comp1_prod")

    # Check return value
    self.assertEqual(returned, "comp1_prod")

  def testCreateProductionVariable(self):

    # Set up test-specific patchers
    findProductionLimitsPatcher = patch.object(pmh.PyomoModelHandler, "_find_production_limits")
    pyoVarPatcher = patch.object(pmh.pyo, "Var") # To check args more easily

    # Start test-specific patchers and store mocks
    mockFindProductionLimits = findProductionLimitsPatcher.start()
    mockPyoVar = pyoVarPatcher.start()

    # Configure mock component and meta
    self.mockComponent1.interaction.capacity_var = "electricity"
    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 0, "h2": 1}}

    ### Scenario 1: Demand, custom tag, add_bounds false, has kwargs, indexer not none, negative cap values

    # Additional setup
    self.mockComponent1.interaction.mock_add_spec(Demand)

    caps = [0, -1, 0, 0]
    mins = [0, -1, -2, -1]
    mockFindProductionLimits.return_value = caps, mins

    # Create PMH instance
    testPMHScen1 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Set indexer
    testPMHScen1.model.comp1_res_index_map = pyo.Set(initialize=[0, 1])

    # Call method under test
    result_prod_name = testPMHScen1._create_production_variable(
      self.mockComponent1,
      tag="custom_prod_var",
      add_bounds=False,
      doc="stuff"
    )

    # Check call to _find_production_limits
    mockFindProductionLimits.assert_called_with(self.mockComponent1)

    # Check that production var was created and set correctly
    mockPyoVar.assert_called_with(
      set([0, 1]),
      set([0, 1, 2, 3]),
      initialize=0,
      bounds=(None, None),
      doc="stuff"
    )
    self.assertEqual(testPMHScen1.model.comp1_custom_prod_var, mockPyoVar.return_value)

    # Check return value
    self.assertEqual(result_prod_name, "comp1_custom_prod_var")

    ### Scenario 2: Producer, default tag and add_bounds, no kwargs, indexer none, positive cap values

    # Additional setup
    self.mockComponent1.interaction.mock_add_spec(Producer)

    caps = [0, 2, 3, 4]
    mins = [0, 1, 0, 2]
    mockFindProductionLimits.return_value = caps, mins

    # Create PMH instance
    testPMHScen2 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Remove indexer
    del testPMHScen1.model.comp1_res_index_map

    # Call method under test
    result_prod_name = testPMHScen2._create_production_variable(self.mockComponent1)

    # Check that resource indexer was set correctly
    resourceIndexer = testPMHScen2.model.comp1_res_index_map
    self.assertSetEqual(resourceIndexer, set([0, 1]))

    # Check call to _find_production_limits
    mockFindProductionLimits.assert_called_with(self.mockComponent1)

    # Check that production var was created and set correctly
    mockPyoVar.assert_called_with(
      testPMHScen2.model.comp1_res_index_map,
      testPMHScen2.model.T,
      initialize=ANY, # Have to check the lambdas for initialize and bounds explicitly, so ignore here
      bounds=ANY
    )

    initializeFunc = mockPyoVar.call_args[1]["initialize"]
    self.assertEqual(initializeFunc.__name__, "<lambda>") # Make sure it's a lambda function
    # Check the function
    self.assertEqual(initializeFunc(0, 2, 0), 0) # r != limit_r(==0)
    self.assertEqual(initializeFunc(0, 0, 3), 2) # r == limit_r == 0

    boundsFunc = mockPyoVar.call_args[1]["bounds"]
    self.assertEqual(boundsFunc.__name__, "<lambda>") # Make sure it's a lambda function
    # Check the function
    self.assertEqual(boundsFunc(0, 2, 0), (None, None)) # r != limit_r(==0)
    self.assertEqual(boundsFunc(0, 0, 3), (2, 4)) # r == limit_r == 0

    self.assertEqual(testPMHScen2.model.comp1_production, mockPyoVar.return_value)

    # Check return value
    self.assertEqual(result_prod_name, "comp1_production")

    ### Scenario 3: bad cap values

    # Mess up caps (mixed signs)
    caps = [0, 2, -3, 4]
    mins = [0, 1, 0, 2]
    mockFindProductionLimits.return_value = caps, mins

    # Create PMH instance
    testPMHScen3 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Call method under test and ensure failure
    with self.assertRaises(AssertionError):
      testPMHScen3._create_production_variable(self.mockComponent1)

  def testCreateRampLimit(self):

    # Configure patchers and mocks

    # Set up fake rule functions
    # This is necessary becuase the lambda functions need real functions to interact with so we can test them
    def fake_ramp_rule_down(prod_name, r, limit, neg_cap, t, m, bins=None):
      return pyo.Constraint.Feasible
    def fake_ramp_rule_up(prod_name, r, limit, neg_cap, t, m, bins=None):
      return pyo.Constraint.Feasible
    def fake_ramp_freq_bins_rule(Bd, Bu, Bn, t, m):
      return pyo.Constraint.Feasible
    def fake_ramp_freq_rule(Bd, Bu, tao, t, m):
      return pyo.Constraint.Feasible

    # Wrap the fake rule functions so we can record the calls to them
    mockFakeRRD = MagicMock(name="mockFakeRampRuleDown", wraps=fake_ramp_rule_down)
    mockFakeRRU = MagicMock(name="mockFakeRampRuleUp", wraps=fake_ramp_rule_up)
    mockFakeRFBR = MagicMock(name="mockFakeRampFreqBinsRule", wraps=fake_ramp_freq_bins_rule)
    mockFakeRFR = MagicMock(name="mockFakeRampFreqRule", wraps=fake_ramp_freq_rule)

    # Update the patched rule library with the wrapped rules
    self.mockPRL.ramp_rule_down = mockFakeRRD
    self.mockPRL.ramp_rule_up = mockFakeRRU
    self.mockPRL.ramp_freq_bins_rule = mockFakeRFBR
    self.mockPRL.ramp_freq_rule = mockFakeRFR

    # Configure mock constraint before starting patcher so .Feasible will refer to original
    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For return values of fake rules
    mockPyoConstraint.side_effect = ["fake_rrd_constr", "fake_rru_constr", "fake_rfbr_constr", "fake_rfr_constr"]

    # Add patchers to track calls to pyo.Constraint and pyo.Var
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)
    pyoVarPatcher = patch.object(pmh.pyo, "Var")

    # Start patchers
    pyoConstraintPatcher.start()
    mockPyoVar = pyoVarPatcher.start()

    # Additional mock configuration
    mockPyoVar.side_effect = ["upVar", "downVar", "steadyVar"]

    self.mockComponent1.interaction.mock_add_spec(Producer)
    self.mockComponent1.interaction.capacity_var = "electricity"
    self.mockComponent1.interaction.ramp_limit = 0.5

    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 0, "h2": 1}}

    ### Scenario 1: cap < 0, ramp_freq > 0

    # Scenario-specific setup
    # FIXME: The below line causes an error because Producer doesn't have a get_capacity method
    self.mockComponent1.interaction.get_capacity.return_value = [{"electricity": -4}]
    self.mockComponent1.interaction.ramp_freq = 3

    # Create PMH instance
    testPMHScen1 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Call method under test
    testPMHScen1._create_ramp_limit(self.mockComponent1, "comp1_production")

    # Check get_capacity call
    self.mockComponent1.interaction.get_capacity.assert_called_with(self.meta)

    # Check that ramp tracker binaries were created and set correctly
    expectedPyoVarCalls = [
      call(set([0, 1, 2, 3]), initialize=0, domain=pyo.Binary),
      call(set([0, 1, 2, 3]), initialize=0, domain=pyo.Binary),
      call(set([0, 1, 2, 3]), initialize=1, domain=pyo.Binary)
    ]
    mockPyoVar.assert_has_calls(expectedPyoVarCalls)

    self.assertEqual(testPMHScen1.model.comp1_up_ramp_tracker, "upVar")
    self.assertEqual(testPMHScen1.model.comp1_down_ramp_tracker, "downVar")
    self.assertEqual(testPMHScen1.model.comp1_steady_ramp_tracker, "steadyVar")

    # Ensure that rules were created and set correctly

    # Check that constraints were created correctly (have to check lambdas separately)
    expectedPyoConstraintCalls = [
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY)
    ]
    mockPyoConstraint.assert_has_calls(expectedPyoConstraintCalls)
    self.assertEqual(mockPyoConstraint.call_count, 4)

    # Extract lambdas from constraint calls and check that they're lambdas
    rrdLambda = mockPyoConstraint.call_args_list[0][1]["rule"]
    self.assertEqual(rrdLambda.__name__, "<lambda>")
    rruLambda = mockPyoConstraint.call_args_list[1][1]["rule"]
    self.assertEqual(rruLambda.__name__, "<lambda>")
    rfbrLambda = mockPyoConstraint.call_args_list[2][1]["rule"]
    self.assertEqual(rfbrLambda.__name__, "<lambda>")
    rfrLambda = mockPyoConstraint.call_args_list[3][1]["rule"]
    self.assertEqual(rfrLambda.__name__, "<lambda>")

    # Call each lambda and check the call args on the mock rule
    rrdLambda("model", 0)
    mockFakeRRD.assert_called_once_with("comp1_production", 0, -2.0, True, 0, "model", bins=("downVar", "upVar", "steadyVar"))
    rruLambda("model", 1)
    mockFakeRRU.assert_called_once_with("comp1_production", 0, -2.0, True, 1, "model", bins=("downVar", "upVar", "steadyVar"))
    rfbrLambda("model", 2)
    mockFakeRFBR.assert_called_once_with("downVar", "upVar", "steadyVar", 2, "model")
    rfrLambda("model", 3)
    mockFakeRFR.assert_called_once_with("downVar", "upVar", 3, 3, "model")

    # Check that constraints were set
    self.assertEqual(testPMHScen1.model.comp1_ramp_down_constr, "fake_rrd_constr")
    self.assertEqual(testPMHScen1.model.comp1_ramp_up_constr, "fake_rru_constr")
    self.assertEqual(testPMHScen1.model.comp1_ramp_freq_binaries, "fake_rfbr_constr")
    self.assertEqual(testPMHScen1.model.comp1_ramp_freq_constr, "fake_rfr_constr")

    ### Scenario 2: cap > 0, ramp_freq = 0

    # Reset mocks
    mockPyoVar.reset_mock()
    mockPyoConstraint.reset_mock()
    mockFakeRRD.reset_mock()
    mockFakeRRU.reset_mock()
    mockFakeRFBR.reset_mock()
    mockFakeRFR.reset_mock()

    mockPyoConstraint.side_effect = ["fake_rrd_constr", "fake_rru_constr"]

    # Scenario-specific setup
    self.mockComponent1.interaction.get_capacity.return_value = [{"electricity": 4}]
    self.mockComponent1.interaction.ramp_freq = 0

    # Create PMH instance
    testPMHScen2 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    # Call method under test
    testPMHScen2._create_ramp_limit(self.mockComponent1, "comp1_production")

    # Check get_capacity call
    self.mockComponent1.interaction.get_capacity.assert_called_with(self.meta)

    # Check that ramp tracker binaries were not created
    mockPyoVar.assert_not_called()

    # Ensure that appropriate rules were created and set correctly

    # Check that constraints were created correctly (have to check lambdas separately)
    expectedPyoConstraintCalls = [
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY)
    ]
    mockPyoConstraint.assert_has_calls(expectedPyoConstraintCalls)
    self.assertEqual(mockPyoConstraint.call_count, 2)

    # Extract lambdas from constraint calls and check that they're lambdas
    rrdLambda = mockPyoConstraint.call_args_list[0][1]["rule"]
    self.assertEqual(rrdLambda.__name__, "<lambda>")
    rruLambda = mockPyoConstraint.call_args_list[1][1]["rule"]
    self.assertEqual(rruLambda.__name__, "<lambda>")

    # Call each lambda and check the call args on the mock rule
    rrdLambda("model", 0)
    mockFakeRRD.assert_called_once_with("comp1_production", 0, 2.0, False, 0, "model", bins=None)
    rruLambda("model", 1)
    mockFakeRRU.assert_called_once_with("comp1_production", 0, 2.0, False, 1, "model", bins=None)

    # Check that constraints were set
    self.assertEqual(testPMHScen1.model.comp1_ramp_down_constr, "fake_rrd_constr")
    self.assertEqual(testPMHScen1.model.comp1_ramp_up_constr, "fake_rru_constr")

    # BUG: What if ramp_limit = 0? Doesn't the `if limit_delta < 0` set neg_cap to True no matter what?
    #      Why aren't we just checking `if cap < 0`?

  def testCreateCapacityConstraints(self):

    # Configure patchers and mocks

    # Set up fake rule functions
    # This is necessary becuase the lambda functions need real functions to interact with so we can test them
    def fake_capacity_rule(prod_name, r, caps, m, t):
      return pyo.Constraint.Feasible
    def fake_min_prod_rule(prod_name, r, caps, minimums, m, t):
      return pyo.Constraint.Feasible

    # Wrap the fake rule functions so we can record the calls to them
    mockFakeCapRule = MagicMock(name="mockFakeRampRuleDown", wraps=fake_capacity_rule)
    mockFakeMinRule = MagicMock(name="mockFakeRampRuleUp", wraps=fake_min_prod_rule)

    # Update the patched rule library with the wrapped rules
    self.mockPRL.capacity_rule = mockFakeCapRule
    self.mockPRL.min_prod_rule = mockFakeMinRule

    # Configure mock constraint before starting patcher so .Feasible will refer to original
    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For return values of fake rules
    mockPyoConstraint.side_effect = ["fake_capacity_constr", "fake_min_prod_constr"]

    # Add patchers
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)
    findProdLimitsPatcher = patch.object(pmh.PyomoModelHandler, "_find_production_limits")

    # Start patchers
    pyoConstraintPatcher.start()
    mockFindProdLimits = findProdLimitsPatcher.start()

    # Additional setup
    self.mockComponent1.interaction.mock_add_spec(Producer)
    self.mockComponent1.interaction.capacity_var = "electricity"

    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 0, "h2": 1}}

    caps = [1, 1, 2, 1]
    mins = [0, 1, 0, 0]
    mockFindProdLimits.return_value = caps, mins

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

    # Set up the production variable
    mockProdVar = MagicMock(name="mockProdVar")
    mockProdVar.get_values.return_value = {(0, 0): 0, (0, 1): 0, (0, 2): 0, (0, 3): 0,
                                           (1, 0): 0, (1, 1): 0, (1, 2): 0, (1, 3): 0 }
    testPMH.model.comp1_production = mockProdVar

    # Call the method under test
    testPMH._create_capacity_constraints(self.mockComponent1, "comp1_production")

    # Check call to _find_production_limits
    mockFindProdLimits.assert_called_once_with(self.mockComponent1)

    # Check that constraints were created correctly (have to check lambdas separately)
    expectedPyoConstraintCalls = [
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY)
    ]
    mockPyoConstraint.assert_has_calls(expectedPyoConstraintCalls)
    self.assertEqual(mockPyoConstraint.call_count, 2)

    # Extract lambdas from constraint calls and check that they're lambdas
    capacityRuleLambda = mockPyoConstraint.call_args_list[0][1]["rule"]
    self.assertEqual(capacityRuleLambda.__name__, "<lambda>")
    minProdLambda = mockPyoConstraint.call_args_list[1][1]["rule"]
    self.assertEqual(minProdLambda.__name__, "<lambda>")

    # Call the lamdas and check call args
    capacityRuleLambda("model", 1)
    mockFakeCapRule.assert_called_once_with("comp1_production", 0, caps, "model", 1)

    minProdLambda("model", 2)
    mockFakeMinRule.assert_called_once_with("comp1_production", 0, caps, mins, "model", 2)

    # Check that constraints were set
    self.assertEqual(testPMH.model.comp1_electricity_capacity_constr, "fake_capacity_constr")
    self.assertEqual(testPMH.model.comp1_electricity_minprod_constr, "fake_min_prod_constr")

    # Check prod var calls
    mockProdVar.get_values.assert_called_once_with() # Called with no args
    # BUG: right now, if the capacity and minimum values are equal for the given resource at any single timestep,
    # then every element of the var, for every resource and every timestep, is set to the capacity value
    # of the resource in question at the last timestep where the capacity equals the minimum
    # mockProdVar.set_values.assert_called_once_with({(0, 0): 1, (0, 1): 1, (0, 2): 1, (0, 3): 1,
    #                                                 (1, 0): 1, (1, 1): 1, (1, 2): 1, (1, 3): 1 })
    # Best guess of intended functionality:
    mockProdVar.set_values.assert_called_once_with({(0, 0): 0, (0, 1): 1, (0, 2): 0, (0, 3): 0,
                                                    (1, 0): 0, (1, 1): 0, (1, 2): 0, (1, 3): 0 })

  def testFindProductionLimits(self):

    # Configure mocks
    self.mockComponent1.interaction.mock_add_spec(Producer)
    self.mockComponent1.interaction.capacity_var = "electricity"
    # FIXME: The below line causes an error because Producer doesn't have a get_capacity method
    self.mockComponent1.interaction.get_capacity.side_effect = [[{"electricity": 4}],
                                                                [{"electricity": 2}],
                                                                [{"electricity": 3}],
                                                                [{"electricity": 1}]]
    self.mockComponent1.interaction.dispatch_flexibility = "independent"
    # FIXME: The below line causes an error because Producer doesn't have a get_minimum method
    self.mockComponent1.interaction.get_minimum.side_effect = [[{"electricity": 1}],
                                                               [{"electricity": 2}],
                                                               [{"electricity": 0}],
                                                               [{"electricity": 1}]]

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
    resultCaps, resultMins = testPMH._find_production_limits(self.mockComponent1)

    # Check get_capacity calls
    self.assertEqual(self.mockComponent1.interaction.get_capacity.call_count, 4)
    # Check last time_index value
    self.assertEqual(self.mockComponent1.interaction.get_capacity.call_args[0][0]["HERON"]["time_index"], 6)

    # Check get_minimum calls
    self.assertEqual(self.mockComponent1.interaction.get_minimum.call_count, 4)
    # Check last time_index value
    self.assertEqual(self.mockComponent1.interaction.get_minimum.call_args[0][0]["HERON"]["time_index"], 6)

    # Check return values
    self.assertEqual(resultCaps, [4, 2, 3, 1])
    self.assertEqual(resultMins, [1, 2, 0, 1])

  def testCreateTransfer(self):

    # Configure patchers and mocks

    createTransferRatioPatcher = patch.object(pmh.PyomoModelHandler, "_create_transfer_ratio")
    createTransferPolyPatcher = patch.object(pmh.PyomoModelHandler, "_create_transfer_poly")

    # Start patchers and store mocks
    mockCreateTransferRatio = createTransferRatioPatcher.start()
    mockCreateTransferPoly = createTransferPolyPatcher.start()

    self.mockComponent1.interaction.mock_add_spec(Interaction)
    mockTransfer = MagicMock(name="mockTransfer")

    # Test with no transfer

    self.mockComponent1.interaction.get_transfer.return_value = None

    # Create PMH instance and call method under test
    testPMH1 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    testPMH1._create_transfer(self.mockComponent1, "comp1_production")

    # Check that nothing was called
    mockCreateTransferRatio.assert_not_called()
    mockCreateTransferPoly.assert_not_called()

    # Test with ratio transfer

    self.mockComponent1.interaction.get_transfer.return_value = mockTransfer

    mockTransfer.mock_add_spec(Ratio)
    # FIXME: The following line causes an error because Ratio doesn't have a type attribute
    mockTransfer.type = "Ratio"

    # Create PMH instance and call method under test
    testPMH2 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    testPMH2._create_transfer(self.mockComponent1, "comp1_production")

    # Check that correct calls were made
    mockCreateTransferRatio.assert_called_once_with(mockTransfer, self.mockComponent1, "comp1_production")
    mockCreateTransferPoly.assert_not_called()

    # Test with poly transfer

    mockCreateTransferRatio.reset_mock()

    mockTransfer.mock_add_spec(Polynomial)
    # FIXME: The following line causes an error because Polynomial doesn't have a type attribute
    mockTransfer.type = "Polynomial"

    # Create PMH instance and call method under test
    testPMH3 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    testPMH3._create_transfer(self.mockComponent1, "comp1_production")

    # Check that correct calls were made
    mockCreateTransferRatio.assert_not_called()
    mockCreateTransferPoly.assert_called_once_with(mockTransfer, self.mockComponent1, "comp1_production")

    # Test with bad transfer

    mockTransfer.type = "Bad"

    # Create PMH instance and call method under test
    testPMH4 = pmh.PyomoModelHandler(
      self.time,
      self.time_offset,
      self.mockCase,
      self.components,
      self.resources,
      self.mockInitialStorage,
      self.meta
    )

    with self.assertRaises(NotImplementedError):
      testPMH4._create_transfer(self.mockComponent1, "comp1_production")

  def testCreateTransferRatio(self):

    # Configure patchers and mocks

    # Set up fake rule function
    # This is necessary becuase the lambda function needs a real function to interact with so we can test it
    def fake_ratio_transfer_rule(ratio, r, ref_r, prod_name, m, t):
      return pyo.Constraint.Feasible

    # Wrap the fake rule function so we can record the calls to it
    mockFakeRTR = MagicMock(name="mockFakeRatioTransferRule", wraps=fake_ratio_transfer_rule)

    # Update the patched rule library with the wrapped rules
    self.mockPRL.ratio_transfer_rule = mockFakeRTR

    # Configure mock constraint before starting patcher so .Feasible will refer to original
    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For return values of fake rule
    mockPyoConstraint.side_effect = ["fake_electricity_rtr_constr", "fake_h2_rtr_constr"]

    # Add and start patcher
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)
    pyoConstraintPatcher.start()

    # Additional setup
    mockTransfer = MagicMock(name="mockTransfer", spec=Ratio)
    mockTransfer.get_coefficients.return_value = {"electricity": 0.8, "h2": 0.4}

    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 0, "h2": 1}}

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

    testPMH._create_transfer_ratio(mockTransfer, self.mockComponent1, "comp1_production")

    # Check get_coefficents call
    mockTransfer.get_coefficients.assert_called_once_with() # With no args

    # Check that constraints were created correctly (have to check lambdas separately)
    expectedPyoConstraintCalls = [
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY)
    ]
    mockPyoConstraint.assert_has_calls(expectedPyoConstraintCalls)
    self.assertEqual(mockPyoConstraint.call_count, 2)

    # Extract lambdas from constraint calls and check that they're lambdas
    elecRTRLambda = mockPyoConstraint.call_args_list[0][1]["rule"]
    self.assertEqual(elecRTRLambda.__name__, "<lambda>")
    h2RTRLambda = mockPyoConstraint.call_args_list[1][1]["rule"]
    self.assertEqual(h2RTRLambda.__name__, "<lambda>")

    # Call the lambdas and check the call args
    elecRTRLambda("model", 1)
    h2RTRLambda("model", 2)

    expectedFakeRTRCalls = [
      call(1, 0, 0, "comp1_production", "model", 1),
      call(2, 1, 0, "comp1_production", "model", 2)
    ]

    mockFakeRTR.assert_has_calls(expectedFakeRTRCalls)

    # Check that constraints were added correctly
    self.assertEqual(testPMH.model.comp1_electricity_electricity_transfer, "fake_electricity_rtr_constr")
    self.assertEqual(testPMH.model.comp1_electricity_h2_transfer, "fake_h2_rtr_constr")

  def testCreateTransferPoly(self):

    # Configure patchers and mocks

    # Set up fake rule function
    # This is necessary becuase the lambda function needs a real function to interact with so we can test it
    def fake_poly_transfer_rule(coeffs, r_map, prod_name, m, t):
      return pyo.Constraint.Feasible

    # Wrap the fake rule function so we can record the calls to it
    mockFakePTR = MagicMock(name="mockFakePolyTransferRule", wraps=fake_poly_transfer_rule)

    # Update the patched rule library with the wrapped rules
    self.mockPRL.poly_transfer_rule = mockFakePTR

    # Configure mock constraint before starting patcher so .Feasible will refer to original
    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For return values of fake rule
    mockPyoConstraint.return_value = "fake_poly_transfer_constr"

    # Add and start patcher
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)
    pyoConstraintPatcher.start()

    # Additional setup
    mockTransfer = MagicMock(name="mockTransfer", spec=Polynomial)
    coeffs = {("electricity", "h2"): {(1, 2): 0.8}}
    mockTransfer.get_coefficients.return_value = coeffs

    self.meta["HERON"]["resource_indexer"] = {self.mockComponent1: {"electricity": 0, "h2": 1}}

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

    testPMH._create_transfer_poly(mockTransfer, self.mockComponent1, "comp1_production")

    # Check get_coefficents call
    mockTransfer.get_coefficients.assert_called_once_with() # With no args

    # Check that constraint was created correctly (have to check lambda separately)
    mockPyoConstraint.assert_called_once_with(set([0, 1, 2, 3]), rule=ANY)

    # Extract lambda from constraint call and check that it's a lambda
    PTRLambda = mockPyoConstraint.call_args[1]["rule"]
    self.assertEqual(PTRLambda.__name__, "<lambda>")

    # Call the lambda and check the call args
    PTRLambda("model", 1)

    mockFakePTR.assert_called_once_with(coeffs, {"electricity": 0, "h2": 1}, "comp1_production", "model", 1)

    # Check that constraint was added correctly
    self.assertEqual(testPMH.model.comp1_transfer_func, "fake_poly_transfer_constr")

  def testCreateStorage(self):

    # Configure patchers and mocks

    # Set up fake rule functions
    # This is necessary becuase the lambda functions need real functions to interact with so we can test them
    def fake_level_rule(comp, level_name, charge_name, discharge_name, initial_storage, r, m, t):
      return pyo.Constraint.Feasible
    def fake_charge_rule(charge_name, bin_name, large_eps, r, m, t):
      return pyo.Constraint.Feasible
    def fake_discharge_rule(discharge_name, bin_name, large_eps, r, m, t):
      return pyo.Constraint.Feasible

    # Wrap the fake rule functions so we can record the calls to them
    mockFakeLevelRule = MagicMock(name="mockFakeLevelRule", wraps=fake_level_rule)
    mockFakeChargeRule = MagicMock(name="mockFakeChargeRule", wraps=fake_charge_rule)
    mockFakeDischargeRule = MagicMock(name="mockFakeDischargeRule", wraps=fake_discharge_rule)

    # Update the patched rule library with the wrapped rules
    self.mockPRL.level_rule = mockFakeLevelRule
    self.mockPRL.charge_rule = mockFakeChargeRule # Unused (disabled) in _create_storage
    self.mockPRL.discharge_rule = mockFakeDischargeRule # Unused (disabled) in _create_storage

    # Configure mock constraint before starting patcher so .Feasible will refer to original
    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For return values of fake rules
    mockPyoConstraint.side_effect = ["fake_level_constr", "fake_charge_constr", "fake_discharge_constr"]

    # Add patchers
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)
    createProdVarPatcher = patch.object(pmh.PyomoModelHandler, "_create_production_variable")

    # Start patchers
    pyoConstraintPatcher.start()
    mockCreateProdVar = createProdVarPatcher.start()

    # Additional setup
    mockCreateProdVar.side_effect = ["comp1_level", "comp1_charge", "comp1_discharge"]

    self.mockComponent1.interaction.apply_periodic_level = True

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

    # Set up fake level_var
    testPMH.model.comp1_level = {(0, 3): 2}

    # Call method under test
    testPMH._create_storage(self.mockComponent1)

    # Last two (charge and discharge) constraints are disabled, so checks for them are commented out

    # Check calls to _create_production_variable
    expectedCreateProdVarCalls = [
      call(self.mockComponent1, tag="level"),
      call(self.mockComponent1, tag="charge", add_bounds=False, within=pyo.NonPositiveReals),
      call(self.mockComponent1, tag="discharge", add_bounds=False, within=pyo.NonNegativeReals)#,
      # call(self.mockComponent1, tag="dcforcer", add_bounds=False, within=pyo.Binary)
    ]
    mockCreateProdVar.assert_has_calls(expectedCreateProdVarCalls)

    # Check that constraints were created correctly (have to check lambdas separately)
    expectedPyoConstraintCalls = [
      call(set([0, 1, 2, 3]), rule=ANY)#,
      # call(set([0, 1, 2, 3]), rule=ANY),
      # call(set([0, 1, 2, 3]), rule=ANY)
    ]
    mockPyoConstraint.assert_has_calls(expectedPyoConstraintCalls)
    self.assertEqual(mockPyoConstraint.call_count, 1)#3)

    # Extract lambdas from constraint calls and check that they're lambdas
    levelRuleLambda = mockPyoConstraint.call_args_list[0][1]["rule"]
    self.assertEqual(levelRuleLambda.__name__, "<lambda>")
    # chargeRuleLambda = mockPyoConstraint.call_args_list[1][1]["rule"]
    # self.assertEqual(chargeRuleLambda.__name__, "<lambda>")
    # dischargeRuleLambda = mockPyoConstraint.call_args_list[2][1]["rule"]
    # self.assertEqual(dischargeRuleLambda.__name__, "<lambda>")

    # Call the lamdas and check call args
    levelRuleLambda("model", 1)
    mockFakeLevelRule.assert_called_once_with(
      self.mockComponent1, "comp1_level", "comp1_charge", "comp1_discharge", 2, 0, "model", 1)

    # chargeRuleLambda("model", 2)
    # mockFakeChargeRule.assert_called_once_with("comp1_charge", "comp1_dcforcer", 1e8, 0, "model", 2)

    # dischargeRuleLambda("model", 3)
    # mockFakeDischargeRule.assert_called_once_with("comp1_discharge", "comp1_dcforcer", 1e8, 0, "model", 3)

    # Check that constraints were set
    self.assertEqual(testPMH.model.comp1_level_constr, "fake_level_constr")
    # self.assertEqual(testPMH.model.comp1_charge_constr, "fake_charge_constr")
    # self.assertEqual(testPMH.model.comp1_discharge_constr, "fake_discharge_constr")

  def testCreateConservation(self):

    # Configure patchers and mocks

    # Set up fake rule function
    # This is necessary becuase the lambda function needs a real function to interact with so we can test it
    def fake_conservation_rule(res, m, t):
      return pyo.Constraint.Feasible

    # Wrap the fake rule function so we can record the calls to it
    mockFakeConservationRule = MagicMock(name="mockFakeConservationRule", wraps=fake_conservation_rule)

    # Update the patched rule library with the wrapped rule
    self.mockPRL.conservation_rule = mockFakeConservationRule

    # Configure mock constraint before starting patcher so .Feasible will refer to original
    mockPyoConstraint = MagicMock(name="mockPyoConstraint")
    mockPyoConstraint.Feasible = pyo.Constraint.Feasible # For return value of fake rule
    mockPyoConstraint.side_effect = ["fake_electricity_conservation_constr", "fake_steam_conservation_constr"]

    # Add patchers
    pyoConstraintPatcher = patch.object(pmh.pyo, "Constraint", mockPyoConstraint)

    # Start patchers
    pyoConstraintPatcher.start()

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
    testPMH._create_conservation()

    # Check that constraints were created correctly (have to check lambdas separately)
    expectedPyoConstraintCalls = [
      call(set([0, 1, 2, 3]), rule=ANY),
      call(set([0, 1, 2, 3]), rule=ANY)
    ]
    mockPyoConstraint.assert_has_calls(expectedPyoConstraintCalls)
    self.assertEqual(mockPyoConstraint.call_count, 2)

    # Extract lambdas from constraint calls and check that they're lambdas
    electricityConservationLambda = mockPyoConstraint.call_args_list[0][1]["rule"]
    self.assertEqual(electricityConservationLambda.__name__, "<lambda>")
    steamConservationLambda = mockPyoConstraint.call_args_list[1][1]["rule"]
    self.assertEqual(steamConservationLambda.__name__, "<lambda>")

    # Call the lamdas and check call args
    electricityConservationLambda("model", 1)
    mockFakeConservationRule.assert_called_with("electricity", "model", 1)

    steamConservationLambda("model", 2)
    mockFakeConservationRule.assert_called_with("steam", "model", 2)

    # Check that constraints were set
    self.assertEqual(testPMH.model.electricity_conservation, "fake_electricity_conservation_constr")
    self.assertEqual(testPMH.model.steam_conservation, "fake_steam_conservation_constr")


if __name__ == "__main__":
  unittest.main()
