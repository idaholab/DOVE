
from .components import Resource, TransferTerm, CashFlow, Source, Sink, Converter, Storage
from .system import System



if __name__ == '__main__':
    funding = Resource("funding")
    labor = Resource("labor")
    work = Resource("work")

    funding_src = Source(
        name="FundingSource",
        capacity_var=funding,
        capacity=200,
        produces=funding,
        dispatch_flexibility="fixed"
    )

    labor_src = Source(
        name="LaborSource",
        capacity_var=labor,
        capacity=500,
        produces=labor
    )

    balance_rat = Converter(
        name="BalanceRatio",
        capacity_var=funding,
        capacity=100,
        produces=work,
        consumes=[funding],
        transfer_terms=[TransferTerm(4, {funding: 1}),
                        TransferTerm(1, {work: 1})]
    )

    quadr = Converter(
        name="Quadratic",
        capacity_var=funding,
        capacity=100,
        produces=work,
        consumes=[funding, labor],
        transfer_terms=[
            TransferTerm(-0.9, {funding: 1}),
            TransferTerm(-1, {labor: 1}),
            TransferTerm(-1e-6, {funding: 1, labor: 2}),
            TransferTerm(-1, {work: 1})
        ]
    )

    milestones = Sink(
        name="Milestones",
        capacity_var=work,
        capacity=6e-3,
        consumes=work,
        cashflows=[CashFlow("proposals", -1)]
    )

    outsrc = Sink(
        name="Outsource",
        capacity_var=funding,
        capacity=150,
        consumes=funding,
        cashflows=[CashFlow("contracts", 1)]
    )

    busy_work = Sink(
        name="BusyWork",
        capacity_var=labor,
        capacity=500,
        consumes=labor,
        cashflows=[CashFlow("other_work", 1)]
    )

    components = [funding_src, labor_src, balance_rat, quadr, milestones, outsrc, busy_work]
    resources = [work, funding, labor]
    sys = System(components, resources)

