from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Any

MARGIN_SHARE = Decimal('0.10')
LOAN_SHARE = Decimal('0.90')


def money(value: Decimal | float | int) -> float:
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Scheme:
    code: str
    name: str
    annual_interest_rate: Decimal
    tenure_years: int
    moratorium_months: int
    max_project_cost: Decimal
    max_loan_amount: Decimal


MICRO = Scheme(
    code='micro_finance',
    name='Micro Finance Scheme',
    annual_interest_rate=Decimal('0.065'),
    tenure_years=3,
    moratorium_months=3,
    max_project_cost=Decimal('140000'),
    max_loan_amount=Decimal('125000'),
)

TERM = Scheme(
    code='term_loan',
    name='Term Loan Scheme',
    annual_interest_rate=Decimal('0.08'),
    tenure_years=7,
    moratorium_months=6,
    max_project_cost=Decimal('5000000'),
    max_loan_amount=Decimal('4500000'),
)


def route_scheme(project_cost: Decimal) -> Scheme | None:
    """Production-rule logic for the prototype. No LLM is involved."""
    if project_cost <= MICRO.max_project_cost:
        return MICRO
    if project_cost <= TERM.max_project_cost:
        return TERM
    return None


def add_months(d: date, months: int) -> date:
    # Avoid external date dependency for this deterministic prototype.
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    month_lengths = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(d.day, month_lengths[month - 1])
    return date(year, month, day)


def generate_quarterly_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_years: int,
    moratorium_months: int,
    start_date: date | None = None,
) -> dict[str, Any]:
    """
    Deterministic quarterly amortization schedule.

    Prototype policy assumption:
    - Total scheme tenure includes the moratorium.
    - During moratorium there are no payments; interest accrues monthly and is capitalized.
    - After moratorium, the remaining tenure is repaid in equal quarterly installments.

    This assumption is explicit so it can later be replaced by the exact lender circular.
    """
    start_date = start_date or date.today()
    monthly_rate = annual_rate / Decimal('12')
    quarterly_rate = annual_rate / Decimal('4')

    # Capitalize monthly interest during moratorium.
    opening_after_moratorium = principal * ((Decimal('1') + monthly_rate) ** moratorium_months)

    total_months = tenure_years * 12
    repayment_months = max(total_months - moratorium_months, 0)
    repayment_quarters = max(1, ceil(repayment_months / 3))

    if quarterly_rate == 0:
        installment = opening_after_moratorium / repayment_quarters
    else:
        q = Decimal('1') + quarterly_rate
        installment = opening_after_moratorium * quarterly_rate * (q ** repayment_quarters) / ((q ** repayment_quarters) - 1)

    rows: list[dict[str, Any]] = []
    balance = opening_after_moratorium
    for i in range(1, repayment_quarters + 1):
        interest = balance * quarterly_rate
        principal_component = installment - interest
        payment = installment
        if i == repayment_quarters or principal_component > balance:
            principal_component = balance
            payment = principal_component + interest
        closing = max(Decimal('0'), balance - principal_component)
        due = add_months(start_date, moratorium_months + i * 3)
        rows.append({
            'installment_no': i,
            'due_date': due.isoformat(),
            'opening_principal': money(balance),
            'interest': money(interest),
            'principal_component': money(principal_component),
            'quarterly_payment': money(payment),
            'closing_principal': money(closing),
        })
        balance = closing

    return {
        'assumption': 'Tenure includes moratorium; moratorium interest is capitalized monthly; repayment is quarterly thereafter.',
        'moratorium_months': moratorium_months,
        'principal_before_moratorium': money(principal),
        'principal_after_moratorium': money(opening_after_moratorium),
        'repayment_quarters': repayment_quarters,
        'quarterly_payment_estimate': money(installment),
        'schedule': rows,
    }


def calculate_financial_plan(margin_capital: float, start_date: date | None = None) -> dict[str, Any]:
    """100% deterministic financial engine. LLMs must never call/replace these calculations."""
    margin = Decimal(str(margin_capital))
    if margin <= 0:
        raise ValueError('Margin capital must be greater than zero.')

    project_cost = margin / MARGIN_SHARE
    ninety_percent_loan = project_cost * LOAN_SHARE
    scheme = route_scheme(project_cost)

    if scheme is None:
        return {
            'eligible': False,
            'reason': 'Calculated project cost exceeds the ₹50,00,000 prototype scheme ceiling.',
            'margin_capital': money(margin),
            'project_cost': money(project_cost),
            'calculated_90_percent_loan': money(ninety_percent_loan),
            'scheme': None,
            'repayment': None,
        }

    # Respect scheme-specific loan ceiling. This only changes the ₹1.40 lakh micro edge case.
    sanctionable_loan = min(ninety_percent_loan, scheme.max_loan_amount)
    financing_gap = max(Decimal('0'), project_cost - margin - sanctionable_loan)

    scheme_dict = asdict(scheme)
    scheme_dict.update({
        'annual_interest_rate': float(scheme.annual_interest_rate * 100),
        'max_project_cost': money(scheme.max_project_cost),
        'max_loan_amount': money(scheme.max_loan_amount),
    })

    return {
        'eligible': True,
        'margin_capital': money(margin),
        'project_cost': money(project_cost),
        'calculated_90_percent_loan': money(ninety_percent_loan),
        'sanctionable_loan': money(sanctionable_loan),
        'financing_gap_due_to_scheme_cap': money(financing_gap),
        'scheme': scheme_dict,
        'repayment': generate_quarterly_schedule(
            sanctionable_loan,
            scheme.annual_interest_rate,
            scheme.tenure_years,
            scheme.moratorium_months,
            start_date=start_date,
        ),
    }
