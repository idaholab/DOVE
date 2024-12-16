"""
Transfer functions describe the balance between consumed and produced
resources for generating components. This module defines the templates
that can be used to describe transfer functions.
"""

import importlib
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))

import DOVE.src._utils as dutils

if importlib.util.find_spec("ravenframework") is None:
  sys.path.append(dutils.get_raven_loc())

# only type references here, as needed
# provide easy name access to module
from .Factory import factory
from .Polynomial import Polynomial
from .Ratio import Ratio
from .TransferFunc import TransferFunc

__all__ = ["TransferFunc", "Ratio", "Polynomial", "factory"]
