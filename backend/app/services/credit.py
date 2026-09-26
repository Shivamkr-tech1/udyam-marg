from __future__ import annotations

from typing import Any


def mock_creditworthiness_score() -> dict[str, Any]:
    """
    DEMO/STUB ONLY.
    Production would require consented, regulated access to utility, UPI and SHG records,
    calibrated models, fairness testing, explainability and lender-compliance review.
    """
    sample = {
        'utility_payment_on_time_ratio': 0.92,
        'upi_monthly_inflow_stability': 0.78,
        'shg_repayment_cycle_score': 0.88,
    }
    weights = {
        'utility_payment_on_time_ratio': 0.35,
        'upi_monthly_inflow_stability': 0.30,
        'shg_repayment_cycle_score': 0.35,
    }
    weighted = sum(sample[k] * weights[k] for k in sample)
    score = round(300 + weighted * 600)
    band = 'Strong' if score >= 750 else 'Moderate' if score >= 650 else 'Developing'
    return {
        'mock': True,
        'score_300_900': score,
        'band': band,
        'sample_features': sample,
        'explanation': 'Illustrative score only; not a bureau score and not suitable for real credit decisions.',
    }
