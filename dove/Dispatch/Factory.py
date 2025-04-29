# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
from .CustomDispatcher import Custom
from .pyomo_dispatch import Pyomo

known = {
  "pyomo": Pyomo,
  "custom": Custom,
}


def get_class(typ):
  """
  Returns the requested dispatcher type.
  @ In, typ, str, name of one of the dispatchers
  @ Out, class, object, class object
  """
  return known.get(typ, None)
