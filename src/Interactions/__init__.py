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
from .Demand import Demand
from .Interaction import Interaction
from .Producer import Producer
from .Storage import Storage

__all__ = ["Interaction", "Producer", "Storage", "Demand"]
