# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Add ``dove`` to system PYTHONPATH for unittests.

This is required because the RAVEN UnitTester navigates to each directory
containing a `tests` file and then runs `python -m unittest <test>` from
within that directory. Python unittests are meant to be run from the top-level
of the repository where it can import the module into its path, but since
we are required to run these tests from within the directory, each test file
needs to establish the location of ``dove`` before it can import it in.
"""
import sys
from os import path, pardir

def resolve_module_path() -> None:
  """
  Add dove to system PYTHONPATH.
  """
  dove_loc_real = path.join(path.dirname(__file__), pardir, pardir)
  sys.path.append(dove_loc_real)

# evaluate on import
resolve_module_path()
