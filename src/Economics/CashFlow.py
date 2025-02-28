from collections import defaultdict
import numpy as np
from ravenframework.utils import InputData, InputTypes


class CashFlow:
  """
  Hold the economics for a single cash flow, C = m * a * (D/D')^x
  where:
    C is the cashflow ($)
    m is a scalar multiplier
    a is the value of the widget, based on the D' volume sold
    D is the amount of widgets sold
    D' is the nominal amount of widgets sold
    x is the scaling factor
  """
  def __repr__(self):
    """
    String representation.
    @ In, None
    @ Out, __repr__, string representation
    """
    return f'<DOVE CashFlow "{self.name}">'
  
  @classmethod
  def get_input_specs(cls):
    """
    Collects input specifications for this class.
    @ In, None
    @ Out, input_specs, InputData, specs
    """
    cf = InputData.parameterInputFactory(
      "CashFlow",
      descr=r"""node for defining a CashFlow for a particular Component.
                This HERON CashFlow will be used to generate a TEAL CashFlow from 
                RAVEN's TEAL plugin. Note a CashFlow generally takes the form 
                $C = \alpha \left(\frac{D}{D'}\right)^x$, aggregated depending on 
                the \xmlAttr{type}. For more information, see the TEAL plugin for 
                RAVEN."""
    )

    cf.addParam(
      "name",
      param_type=InputTypes.StringType,
      required=True,
      descr=r"""the name by which this CashFlow will be identified as
                part of this component. The general name is prefixed by the component
                name, such as ComponentName$\vert$CashFlowName. """,
    )

    cf.addParam(
      "type",
      param_type=InputTypes.makeEnumType("CFType", "CFType", ["one-time", "repeating"]),
      required=True,
      descr=r"""the type of CashFlow to calculate. \xmlString{one-time}
                is suitable for capital expenditure CashFlows, while \xmlString{repeating}
                is used for repeating costs such as operations and maintenance
                (fixed or variable), market sales, or similar.""",
    )

    cf.addParam(
      "taxable",
      param_type=InputTypes.BoolType,
      required=True,
      descr=r"""determines whether this CashFlow is taxed every cycle.""",
    )

    cf.addParam(
      "inflation",
      param_type=InputTypes.StringType,
      required=True,
      descr=r"""determines how inflation affects this CashFlow every cycle.
                See the CashFlow submodule of RAVEN.""",
    )

    cf.addParam(
      "mult_target",
      param_type=InputTypes.BoolType,
      required=False,
      descr=r"""\WARNING{DEPRECATED} indicates whether this parameter should be
                a target of the multiplication factor for NPV matching analyses.
                This parameter is no longer operational. Specifying it in an input
                file does nothing. To access the equivalent feature users should
                now specify within the desired Cash Flow: under the ``reference price''
                node a ``levelized cost'' subnode.""",
    )

    cf.addParam(
      "npv_exempt",
      param_type=InputTypes.BoolType,
      required=False,
      default=False,
      descr=r"""indicates whether this CashFlow should be exempt from
                Net Present Value (NPV) calculations. Setting this parameter to
                ``True'' will allow the CashFlow to be used within the dispatch
                optimization, but will be left out of the finanical computations.
                Thus, users can leverage this feature to motivate the dispatch
                optimization without affecting the financial results. \WARNING{WARNING}:
                this is an advanced feature that changes the interpretations of
                the results typically generated by HERON. Use with caution!""",
    )

    cf.addParam(
      "period",
      param_type=InputTypes.makeEnumType(
        "period_opts", "period_opts", ["hour", "year"]
      ),
      required=False,
      descr=r"""for a \xmlNode{CashFlow} with \xmlAttr{type} \xmlString{repeating},
                indicates whether the CashFlow repeats every time step (\xmlString{hour})
                or every cycle (\xmlString{year})). Generally, CashFlows such as fixed
                operations and maintenance costs are per-cycle, whereas variable costs
                such as fuel and maintenance as well as sales are repeated every time step.""",
    )

    driver = InputData.parameterInputFactory(
      "driver",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""indicates the main driver for this CashFlow, such as the number of 
                units sold or the size of the constructed unit. Corresponds to $D$ 
                in the CashFlow equation.""",
    )
    cf.addSub(driver)

    reference_price = InputData.parameterInputFactory(
      "reference_price",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""indicates the cash value of the reference number of units sold.
                corresponds to $\alpha$ in the CashFlow equation. If \xmlNode{reference_driver}
                is 1, then this is the price-per-unit for the CashFlow.""",
    )

    levelized_cost = InputData.parameterInputFactory(
      "levelized_cost",
      strictMode=True,
      descr=r"""indicates whether HERON and TEAL are meant to solve for the levelized 
                price related to this cashflow.""",
    )

    reference_price.addSub(levelized_cost)
    cf.addSub(reference_price)

    reference_driver = InputData.parameterInputFactory(
      "reference_driver",
      contentType=InputTypes.FloatOrIntType,
      descr=r"""determines the number of units sold to which the \xmlNode{reference_price}
                refers. Corresponds to $\prime D$ in the CashFlow equation.""",
    )
    cf.addSub(reference_driver)

    x = InputData.parameterInputFactory(
      "scaling_factor_x",
      contentType=InputTypes.FloatType,
      descr=r"""determines the scaling factor for this CashFlow. Corresponds to 
                $x$ in the CashFlow equation. If $x$ is less than one, the per-unit 
                price decreases as the units sold increases above the \xmlNode{reference_driver}, 
                and vice versa.""",
    )
    cf.addSub(x)

    depreciate = InputData.parameterInputFactory(
      "depreciate",
      contentType=InputTypes.IntegerType,
      descr=r"""indicates the number of cycles over which this CashFlow should be 
                depreciated. Depreciation schemes are assumed to be MACRS and available 
                cycles are listed in the CashFlow submodule of RAVEN.""",
    )
    cf.addSub(depreciate)

    return cf

  def __init__(self, component=None):
    """
    Constructor
    @ In, component, CashFlowUser instance, cash flow user to which this cash flow belongs
    @ Out, None
    """
    # assert component is not None # TODO is this necessary? What if it's not a component-based cash flow?
    self._component = (component)  # component instance to whom this cashflow belongs, if any
    # equation values
    self._driver = None  # ValuedParam "quantity produced", D
    self._alpha = None  # ValuedParam "price per produced", a
    self._reference = None  # ValuedParam "where price is accurate", D'
    self._scale = None  # ValuedParam "economy of scale", x
    # other params
    self.name = None  # base name of cash flow
    self._type = None  # needed? one-time, yearly, repeating
    self._taxable = None  # apply tax or not
    self._inflation = None  # apply inflation or not
    self._mult_target = None  # not clear
    self._npv_exempt = None  # inlcude cashflow in NPV calculation
    self._depreciate = None
    self._period = None  # period for recurring cash flows
    # other members
    self._signals = set()  # variable values needed for this cash flow
    self._crossrefs = defaultdict(dict)

  def _set_value(self, name, spec):
    """
    """
    setattr(self, name, spec.value)

  def read_input(self, item):
    """
    Sets settings from input file
    @ In, item, InputData.ParameterInput, parsed specs from user
    @ Out, None
    """
    self.name = item.parameterValues["name"]
    # handle type directly here momentarily
    self._taxable = item.parameterValues["taxable"]
    self._inflation = item.parameterValues["inflation"]
    self._type = item.parameterValues["type"]
    self._period = item.parameterValues.get("period", "hour")
    self._npv_exempt = item.parameterValues.get("npv_exempt", False)
    # the remainder of the entries are ValuedParams, so they'll be evaluated as-needed
    for sub in item.subparts:
      # Magic variables are dumb, but here we are. 
      name = "_" + sub.getName()
      if name == "_depreciate":
        self._depreciate = sub.value
      elif name == "_reference_price":
        price_is_levelized = self.set_reference_price(sub)
      elif name in ["_driver", "_reference_driver", "_scaling_factor_x"]:
        self._set_value(name, sub)
      else:
        raise IOError(f"Unrecognized 'CashFlow' node: {sub.getName()}")

    # resolve levelized cost
    self._mult_target = price_is_levelized
    # user asked to find Time Invariant levelized cost
    if self._alpha is None and price_is_levelized:
      self._set_fixed_param("_alpha", 1)

    # driver is required!
    if self._driver is None:
      raise IOError(f"No <driver> node provided for CashFlow {self.name}!")

    # defaults
    var_names = ["_reference", "_scale"]
    for name in var_names:
      if getattr(self, name) is None:
        # setattr(self, name, 1)
        # TODO raise a warning?
        self._set_fixed_param(name, 1)

  def set_reference_price(self, node):
    """
    Sets the reference_price attribute based on given ValuedParam or if Levelized Cost
    @ In, node, InputParams.ParameterInput, reference_price head node
    @ Out, price_is_levelized, bool, are we computing levelized cost for this cashflow?
    """
    levelized_cost = False
    for sub in node.subparts:
      if sub.name == "levelized_cost":
        levelized_cost = True
        __ = node.popSub("levelized_cost")

    try:
      self._set_value("_alpha", node)
    except AttributeError as e:
      if levelized_cost:
        self._set_fixed_param("_alpha", 1)
      else:
        raise IOError(
          f"No <reference_price> node provided for CashFlow {self.name}!"
        ) from e
    price_is_levelized = bool(levelized_cost)
    return price_is_levelized

  # Not none set it to default 1
  def get_period(self):
    """
    Getter for Recurring cashflow period type.
    @ In, None
    @ Out, period, str, 'hourly' or 'yearly'
    """
    return self._period

  def get_alpha_extension(self):
    """
    creates multiplier for the valued shape the alpha cashflow parameter should be in
    @ In, None,
    @ Out, ext, multiplier for "alpha" values based on CashFlow type
    """
    life = self._component.get_economics().get_lifetime()
    if self._type == "one-time":
      ext = np.zeros(life + 1, dtype=float)
      ext[0] = 1.0
    elif self._type == "repeating":
      ext = np.ones(life + 1, dtype=float)
      ext[0] = 0.0
    else:
      raise NotImplementedError(f"type is: {self._type}")
    return ext

  def get_crossrefs(self):
    """
    Accessor for cross-referenced entities needed by this cashflow.
    @ In, None
    @ Out, crossrefs, dict, cross-referenced requirements dictionary
    """
    return self._crossrefs

  def set_crossrefs(self, refs):
    """
    Setter for cross-referenced entities needed by this cashflow.
    @ In, refs, dict, cross referenced entities
    @ Out, None
    """
    # set up pointers
    for attr, obj in refs.items():
      valued_param = self._crossrefs[attr]
      valued_param.set_object(obj)
    # check on VP setup
    for attr, vp in self._crossrefs.items():
      vp.crosscheck(self._component.get_interaction())

  def evaluate_cost(self, activity, values_dict):
    """
    Evaluates cost of a particular scenario provided by "activity".
    @ In, activity, pandas.Series, multi-indexed array of scenario activities
    @ In, values_dict, dict, additional values that may be needed to evaluate cost
    @ In, t, int, time index at which cost should be evaluated
    @ Out, cost, float, cost of activity
    """
    # note this method gets called a LOT, so speedups here are quite effective
    # add the activity to the dictionary
    values_dict["HERON"]["activity"] = activity
    params = self.calculate_params(values_dict)
    return params["cost"]

  def calculate_params(self, values_dict):
    """
    Calculates the value of the cash flow parameters.
    @ In, values_dict, dict, mapping from simulation variable names to their values (as floats or numpy arrays)
    @ Out, params, dict, dictionary of parameters mapped to values including the cost
    """
    # TODO maybe don't cast these as floats, as they could be symbolic expressions (seems unlikely)
    Dp = float(self._reference.evaluate(values_dict, target_var="reference_driver")[0]["reference_driver"])
    x = float(self._scale.evaluate(values_dict, target_var="scaling_factor_x")[0]["scaling_factor_x"])
    a = self._alpha.evaluate(values_dict, target_var="reference_price")[0]["reference_price"]
    D = self._driver.evaluate(values_dict, target_var="driver")[0]["driver"]
    cost = a * (D / Dp) ** x
    params = {
      "alpha": a,
      "driver": D,
      "ref_driver": Dp,
      "scaling": x,
      "cost": cost,
    }  # TODO float(cost) except in pyomo it's not a float
    return params

  #######
  # API #
  #######
  def get_price(self):
    """
    Getter for Cashflow Price
    @ In, None
    @ Out, alpha, ValuedParam, valued param for the cash flow price
    """
    return self._alpha

  def get_driver(self):
    """
    Getter for Cashflow Driver
    @ In, None
    @ Out, driver, ValuedParam, valued param for the cash flow driver
    """
    return self._driver

  def get_reference(self):
    """
    Getter for Cashflow Reference Driver
    @ In, None
    @ Out, reference, ValuedParam, valued param for the cash flow reference driver
    """
    return self._reference

  def get_scale(self):
    """
    Getter for Cashflow Scale
    @ In, None
    @ Out, scale, ValuedParam, valued param for the cash flow economy of scale
    """
    return self._scale

  def get_type(self):
    """
    Getter for Cashflow Type
    @ In, None
    @ Out, type, str, one-time, yearly, repeating
    """
    return self._type

  def get_depreciation(self):
    """
    Getter for Cashflow depreciation
    @ In, None
    @ Out, depreciate, int or None
    """
    return self._depreciate

  def is_taxable(self):
    """
    Getter for Cashflow taxable boolean
    @ In, None
    @ Out, taxable, bool, is cashflow taxable?
    """
    return self._taxable

  def is_inflation(self):
    """
    Getter for Cashflow inflation boolean
    @ In, None
    @ Out, inflation, bool, is inflation applied to cashflow?
    """
    return self._inflation

  def is_mult_target(self):
    """
    Getter for Cashflow mult_target boolean
    @ In, None
    @ Out, taxable, bool, is cashflow a multiplier target?
    """
    return self._mult_target

  def is_npv_exempt(self):
    """
    Getter for Cashflow npv_exempt boolean
    @ In, None
    @ Out, npv_exempt, bool, is cashflow exempt from NPV calculations?
    """
    return self._npv_exempt
