# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Component Module
"""

from collections import defaultdict

DESCRIPTIONS = defaultdict(dict)

DESCRIPTIONS["Component"] = {
  "descr": r"""defines a component as an element of the grid system.
                Components are defined by the action they perform such as
                \xmlNode{produces} or \xmlNode{consumes}; see details below.
            """,
  "name": r"""
      identifier for the component. This identifier will be used to
      generate variables and relate signals to this component throughout
      the DOVE analysis.
      """,
}

DESCRIPTIONS["Interaction"] = {
  "resource": ddd,
  "dispatch": r"""
      describes the way this component should be dispatched, or its flexibility.
      \texttt{fixed} indicates the component always fully dispatched at
      its maximum level. \texttt{independent} indicates the component is
      fully dispatchable by the dispatch optimization algorithm.
      \texttt{dependent} indicates that while this component is not directly
      controllable by the dispatch algorithm, it can however be flexibly
      dispatched in response to other units changing dispatch level.
      For example, when attempting to increase profitability, the
      \texttt{fixed} components are not adjustable, but the \texttt{independent}
      components can be adjusted to attempt to improve the economic metric.
      In response to the \texttt{independent} component adjustment, the
      \texttt{dependent} components may respond to balance the resource
      usage from the changing behavior of other components.
      """,
}

DESCRIPTIONS["produces"] = {
  "consumes": ...,
  "ramp_limit": ...,
  "ramp_freq": ...,
}

DESCRIPTIONS["transfer"] = {}
