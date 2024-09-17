import unittest
from unittest.mock import MagicMock, call, patch, ANY

from ravenframework.utils import InputData

from DOVE.src.Components import Component



class TestComponent(unittest.TestCase):
  @patch("ravenframework.utils.InputData.parameterInputFactory")
  @patch("DOVE.src.Interactions.Producer.get_input_specs")
  @patch("DOVE.src.Interactions.Storage.get_input_specs")
  @patch("DOVE.src.Interactions.Demand.get_input_specs")
  @patch("DOVE.src.Economics.CashFlowGroup.get_input_specs")
  def test_get_input_specs(
    self,
    mock_cashflow_get_input_specs,
    mock_demand_get_input_specs,
    mock_storage_get_input_specs,
    mock_producer_get_input_specs,
    mock_parameter_input_factory,
  ):
    # Set up the MagicMock objects
    mock_specs = MagicMock()
    mock_parameter_input_factory.return_value = mock_specs

    mock_prod_specs = MagicMock(name="ProducerSpecs")
    mock_stor_specs = MagicMock(name="StorageSpecs")
    mock_demand_specs = MagicMock(name="DemandSpecs")
    mock_cashflow_specs = MagicMock(name="CashFlowSpecs")

    mock_producer_get_input_specs.return_value = mock_prod_specs
    mock_storage_get_input_specs.return_value = mock_stor_specs
    mock_demand_get_input_specs.return_value = mock_demand_specs
    mock_cashflow_get_input_specs.return_value = mock_cashflow_specs

    # Call the method under test
    specs = Component.get_input_specs()

    # Assertions to verify behavior
    mock_parameter_input_factory.assert_called_once_with(
      "Component", ordered=False, baseNode=None, descr=ANY
    )

    # Check if the 'name' parameter was added correctly
    mock_specs.addParam.assert_called_once_with(
      "name", param_type=InputData.InputTypes.StringType, required=True, descr=ANY
    )

    # Check that all sub-specifications were added
    expected_calls = [
      call(mock_prod_specs),
      call(mock_stor_specs),
      call(mock_demand_specs),
      call(mock_cashflow_specs),
    ]
    mock_specs.addSub.assert_has_calls(expected_calls, any_order=True)

    # Check the returned value
    self.assertEqual(specs, mock_specs)


if __name__ == "__main__":
  unittest.main()
