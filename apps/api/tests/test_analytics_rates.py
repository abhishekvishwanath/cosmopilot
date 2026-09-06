"""
Unit coverage for the funnel rate math (app/services/analytics.py). The
DB-aggregate queries themselves (app/repositories/analytics.py) are
verified live against the real Supabase project, same as every other
DB-integrated piece of this backend — see the Phase 11 report.
"""

from app.services.analytics import _safe_rate


def test_safe_rate_returns_none_for_zero_denominator() -> None:
    assert _safe_rate(0, 0) is None
    assert _safe_rate(5, 0) is None


def test_safe_rate_computes_rounded_ratio() -> None:
    assert _safe_rate(1, 3) == 0.3333
    assert _safe_rate(2, 4) == 0.5
    assert _safe_rate(0, 10) == 0.0
