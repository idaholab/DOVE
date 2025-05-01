# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Values that are expressed as linear ratios of one another.
Primarily intended for transfer functions.
"""
import warnings
import numpy as np
from .transfer import TransferFunc


# class for custom dynamically-evaluated quantities
class Ratio(TransferFunc):
  """
  Represents a TransferFunc that uses a linear balance of resources, such as 3a + 7b -> 2c.
  This means the ratios of the resources must be maintained, NOT 3a + 7b = 2c!
  """

  def __init__(self, coefficients: dict):
    """
    Constructor.
    @ In, None
    @ Out, None
    """
    super().__init__()
    self.coefficients = coefficients

  def read(self, comp_name, spec):
    """
    Used to read transfer func from XML input
    @ In, comp_name, str, name of component that this valued param will be attached to; only used for print messages
    @ In, spec, InputData params, input specifications
    @ Out, None
    """
    super().read(comp_name, spec)
    self._coefficients = {}
    node = spec.findFirst("ratio")
    # ALIAS SUPPORT
    if node is None:
      node = spec.findFirst("linear")
      if node is None:
        raise IOError(f'Unrecognized transfer function for component "{comp_name}": "{spec.name}"')
      warnings.warn('"linear" has been deprecated and will be removed in the future; see "ratio" transfer function!')

    for rate_node in node.findAll("rate"):
      resource = rate_node.parameterValues["resource"]
      self._coefficients[resource] = rate_node.value

  def get_resources(self):
    """
    Provides the resources used in this transfer function.
    @ In, None
    @ Out, resources, set, set of resources used
    """
    return set(self._coefficients.keys())

  def get_coefficients(self):
    """
    Returns linear coefficients.
    @ In, None
    @ Out, coeffs, dict, coefficient mapping
    """
    return self._coefficients

  def set_io_signs(self, consumed, produced):
    """
    Fix up input/output signs, if interpretable
    @ In, consumed, list, list of resources consumed in the transfer
    @ In, produced, list, list of resources produced in the transfer
    @ Out, None
    """
    for res, coef in self.get_coefficients().items():
      if res in consumed:
        self._coefficients[res] = -np.abs(coef)
      elif res in produced:
        self._coefficients[res] = np.abs(coef)
      else:
        # should not be able to get here after IO gets checked!
        raise RuntimeError(
          'While checking transfer coefficient, resource "{res}" was neither consumed nor produced!'
        )
