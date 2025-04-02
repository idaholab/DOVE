import __init__ # Running __init__ here enables importing from DOVE and RAVEN

import unittest

from DOVE.src.TransferFuncs import TransferFunc

class TestTransferFunc(unittest.TestCase):

  def testCheckIO(self):

    # Set up example TransferFunc
    class exampleTransferFunc(TransferFunc):
      def get_resources(self):
        used = ["electricity", "H2"]
        return set(used)

    # Create TransferFunc instance
    testTransferFunc = exampleTransferFunc()

    # Set io values
    good_inputs = ["electricity", "H2"]
    good_outputs = ["electricity", "H2"]

    excess_inputs = ["electricity", "H2", "heat"]
    excess_outputs = ["electricity", "H2", "heat"]

    insufficient_inputs = ["electricity"]
    insufficient_outputs = ["electricity"]

    # Call the method under test with good io values
    # Ensure method does not throw error
    testTransferFunc.check_io(good_inputs, good_outputs, "CompName")

    # Call the method under test with excess inputs
    with self.assertRaises(IOError):
      testTransferFunc.check_io(excess_inputs, good_outputs, "CompName")

    # Call the method under test with excess outputs
    with self.assertRaises(IOError):
      testTransferFunc.check_io(good_inputs, excess_outputs, "CompName")

    # Call the method under test with insufficient inputs and outputs
    with self.assertRaises(IOError):
      testTransferFunc.check_io(insufficient_inputs, insufficient_outputs, "CompName")


if __name__ == "__main__":
  unittest.main()
