"""
utilities for use within dove
"""

import importlib
import sys
import xml.etree.ElementTree as ET
from os import path


def get_raven_loc():
  """
  Return RAVEN location, either from pip or from DOVE config file
  @ In, None
  @ Out, loc, string, absolute location of RAVEN
  """
  spec = importlib.util.find_spec("ravenframework")
  if spec is not None:
    return path.abspath(path.dirname(spec.origin))

  # If we made it this far, then RAVEN is not pip installed and should be cloned
  # locally. We also expect that users will have installed DOVE as a plugin to RAVEN.
  # This means there exists a .ravenconfig.xml file in the top level of DOVE.
  config = path.abspath(path.join(path.dirname(__file__), "..", ".ravenconfig.xml"))
  if not path.isfile(config):
    raise IOError(
      f'DOVE config file not found at "{config}"! Has DOVE been installed as a plugin in a RAVEN installation?'
    )

  loc = ET.parse(config).getroot().find("FrameworkLocation")
  if loc is None or loc.text is None:
    raise AssertionError("RAVEN location not found in .ravenconfig.xml!")
  # The addition of ravenframework as an installable package requires
  # adding the raven directory to the PYTHONPATH instead of adding
  # ravenframework. We will expect '.ravenconfig.xml' to point to
  # raven/ravenframework always, so this is why we grab the parent dir.
  return path.abspath(path.dirname(loc.text))


def get_cashflow_loc(raven_path=None):
  """
  Get CashFlow (aka TEAL) location in installed RAVEN
  @ In, raven_path, string, optional, if given then start with this path
  @ Out, cf_loc, string, location of CashFlow
  """
  if raven_path is None:
    raven_path = get_raven_loc()
  plugin_handler_dir = path.join(raven_path, "scripts")
  sys.path.append(plugin_handler_dir)
  sys.path.append(path.join(raven_path, "scripts"))
  plugin_handler = importlib.import_module("plugin_handler")
  sys.path.pop()
  sys.path.pop()
  cf_loc = plugin_handler.getPluginLocation("TEAL")
  return cf_loc
