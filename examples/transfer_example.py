# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
"""
import dove.core as dc

if __name__ == '__main__':
  funding = dc.Resource("funding")
  labor = dc.Resource("labor")
  work = dc.Resource("work")

  funding_source = dc.Source(
    name="FundingSource",
    produces=funding,
    max_capacity=200,
    flexibility="fixed",
  )

  labor_source = dc.Source(
    name="LaborSource",
    produces=labor,
    max_capacity=500,
    flexibility="fixed",
  )

  balance_ratio = dc.Converter(
    name="BalanceRatio",
    consumes=[funding],
    produces=[work],
    capacity_resource=funding,
    max_capacity=100,
    transfer_fn=dc.RatioTransfer(funding, work, 0.25)
  )

  quadratic = dc.Converter(
    name="Quadratic",
    consumes=[funding, labor],
    produces=[work],
    capacity_resource=funding,
    max_capacity=100,
    transfer_fn=dc.PolynomialTransfer([
      (0.9, {funding: 1}),
      (1, {labor: 1}),
      (1e-6, {funding: 1, labor: 2}),
    ])
  )

  work_sink = dc.Sink(
    name="Milestones",
    consumes=work,
    max_capacity=6e3,
    cashflows=[dc.Revenue("proposals", alpha=1.0)]
  )

  funding_sink = dc.Sink(
    name="Outsource",
    consumes=funding,
    max_capacity=150,
    cashflows=[dc.Cost("contracts", alpha=1.0)]
  )

  labor_sink = dc.Sink(
    name="BusyWork",
    consumes=labor,
    max_capacity=500,
    cashflows=[dc.Cost("other_work", alpha=1.0)]
  )

  sys = dc.System(
    components=[
      funding_source,
      labor_source,
      balance_ratio,
      quadratic,
      work_sink,
      funding_sink,
      labor_sink
    ],
    resources=[funding, labor, work],
  )
  results = sys.solve(solver="ipopt")
  print(results)
  results.to_csv("example_transfers.csv")