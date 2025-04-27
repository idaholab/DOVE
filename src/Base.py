# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Base classes for other classes.
"""

from ravenframework.BaseClasses import MessageUser
from ravenframework.MessageHandler import MessageHandler


class Base(MessageUser):
  def __init__(self, **kwargs):
    """
    Constructor.
    @ In, kwargs, dict, passthrough arguments
    @ Out, None
    """
    super().__init__()
    mh = MessageHandler()
    mh.initialize(
      {
        "verbosity": "all",
        "callerLength": 18,
        "tagLength": 7,
        "suppressErrs": False,
      }
    )
    self.messageHandler = kwargs.get("messageHandler", mh)

  def __repr__(self):
    """
    String representation.
    @ In, None
    @ Out, repr, str rep
    """
    return f"<DOVE {self.__class__.__name__}>"

  def set_message_handler(self, mh):
    """
    Sets message handling tool.
    @ In, mh, MessageHandler, message handler
    @ Out, None
    """
    self.messageHandler = mh
