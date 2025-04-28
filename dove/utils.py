# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
utilities for use within dove
"""
from importlib.util import find_spec
from os.path import abspath, dirname, isfile, join

def get_raven_loc() -> str:
  """
  Return RAVEN location, either from pip or from DOVE config file
  @ In, None
  @ Out, loc, string, absolute location of RAVEN
  """
  spec = find_spec("ravenframework")
  if spec is not None and spec.origin is not None:
      return abspath(dirname(spec.origin))

  # If we made it this far, then RAVEN is not pip installed and should be cloned
  # locally. We also expect that users will have installed DOVE as a plugin to RAVEN.
  # This means there exists a .ravenconfig.xml file in the top level of DOVE.
  config = abspath(join(dirname(__file__), "..", ".ravenconfig.xml"))
  if not isfile(config):
    raise IOError(
      f"DOVE config file not found at '{config}'! Has DOVE been installed as a plugin in a RAVEN installation?"
    )
  
  import xml.etree.ElementTree as ET
  loc = ET.parse(config).getroot().find("FrameworkLocation")
  if loc is None or loc.text is None:
    raise AssertionError("RAVEN location not found in .ravenconfig.xml!")
  # The addition of ravenframework as an installable package requires
  # adding the raven directory to the PYTHONPATH instead of adding
  # ravenframework. We will expect '.ravenconfig.xml' to point to
  # raven/ravenframework always, so this is why we grab the parent dir.
  return abspath(dirname(loc.text))
