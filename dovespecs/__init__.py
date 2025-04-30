# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
``dove.inputspec``
===================
"""
from importlib.util import find_spec
# ravenframework could be pip-installed or located elsewhere.
if find_spec("ravenframework") is None:
  import sys
  from dove.utils import get_raven_loc
  # Add ravenframework to the PYTHONPATH
  sys.path.append(get_raven_loc())

# from .autospec import AutoSpec

# __all__ = ["AutoSpec"]