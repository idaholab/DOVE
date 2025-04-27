# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Transfer functions describe the balance between consumed and produced
resources for generating components. This module defines the templates
that can be used to describe transfer functions.
"""

import importlib
import os
import sys

dove_loc_import = importlib.util.find_spec("DOVE") # This is none if DOVE is not in the path
dove_loc_real = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
if dove_loc_import is not dove_loc_real: # DOVE was not found or the wrong DOVE was found
  sys.path.append(dove_loc_real)

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
