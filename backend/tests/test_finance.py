from datetime import date

from app.services.finance import calculate_financial_plan


def test_sample_flow_term_loan():
    result = calculate_financial_plan(100000, start_date=date(2026, 9, 26))
    assert result['eligible'] is True
    assert result['project_cost'] == 1000000.0
    assert result['calculated_90_percent_loan'] == 900000.0
    assert result['sanctionable_loan'] == 900000.0
    assert result['scheme']['name'] == 'Term Loan Scheme'
    assert result['scheme']['annual_interest_rate'] == 8.0
    assert result['scheme']['tenure_years'] == 7
    assert result['scheme']['moratorium_months'] == 6
    assert len(result['repayment']['schedule']) == 26


def test_micro_scheme_cap_is_respected():
    result = calculate_financial_plan(14000, start_date=date(2026, 9, 26))
    assert result['project_cost'] == 140000.0
    assert result['calculated_90_percent_loan'] == 126000.0
    assert result['sanctionable_loan'] == 125000.0
    assert result['financing_gap_due_to_scheme_cap'] == 1000.0
    assert result['scheme']['name'] == 'Micro Finance Scheme'


def test_over_ceiling_is_ineligible():
    result = calculate_financial_plan(600000)
    assert result['eligible'] is False
    assert result['project_cost'] == 6000000.0
