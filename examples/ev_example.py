import dove.core as dc

# Resources
electricity = dc.Resource(name="electricity")

# This is not a physical resource. We're just using it as a tracking mechanism
charging_completed = dc.Resource(name="charging_completed")

### Time series data
TIME = 4
max_production = [30.0] * TIME
max_consumption = [10.0, 20.0, 30.0, 20.0]
min_consumption = [0.0, 5.0, 10.0, 5.0]

### Main components

# Example source
electricity_source = dc.Source(
    name="electricity_source",
    produces=electricity,
    max_capacity_profile=max_production,
    flexibility="flex",
)

# This Sink has been changed to a Converter. This is so it can produce the charging_completed
# resource that we want to use for tracking how much the EVs have charged thus far
ev_charging = dc.Converter(
    name="ev_charging",
    consumes=[electricity],
    produces=[charging_completed],
    capacity_resource=electricity,
    max_capacity_profile=max_consumption,
    min_capacity_profile=min_consumption,
    transfer_fn=dc.RatioTransfer(
        input_resources={electricity: 1.0}, output_resources={charging_completed: 1.0}
    ),
    flexibility="flex",
    cashflows=[dc.Revenue(name="motivating_cashflow", alpha=1.0)],
)

### Extra, fake components used for tracking and enforcing charging

# This component serves to track the total amount of charging that has been completed thus far
# This works because every resource has to be conserved, and for every timestep but the last, this
# is the only component that can consume the charging_completed from the ev_charging component
cumulative_charging_tracker = dc.Storage(
    name="cumulative_charging_tracker",
    resource=charging_completed,
    max_capacity_profile=[50.0] * TIME,  # Can hold up to 50 units of completed charging
    periodic_level=True,  # Means that it has to discharge everything by the end of the time
    initial_stored=0,
)

# This component MUST consume exactly 50 units of charging_completed at the final timestep
# This means that, by the final timestep, 50 units of charging_completed must have been accumulated
# The only way to produce charging_completed is by the ev_charging component consuming electricity
# So this forces the ev_charging component to consume exactly 50 units of electricity through the
# full time period
total_charge_confirmation = dc.Sink(
    name="total_charge_confirmation",
    consumes=charging_completed,
    max_capacity_profile=[0.0, 0.0, 0.0, 50.0],
    flexibility="fixed",
)

### System creation and solution

sys = dc.System(
    components=[
        electricity_source,
        ev_charging,
        cumulative_charging_tracker,
        total_charge_confirmation,
    ],
    resources=[electricity, charging_completed],
    time_index=list(range(TIME)),
)

results = sys.solve("price_taker")
print(results)
