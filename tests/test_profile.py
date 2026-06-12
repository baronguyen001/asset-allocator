from __future__ import annotations

from asset_allocator.profile import build_profile, classify, risk_score, run_questionnaire


def test_classify_boundaries() -> None:
    assert classify(0) == "conservative"
    assert classify(34) == "conservative"
    assert classify(35) == "balanced"
    assert classify(59) == "balanced"
    assert classify(60) == "growth"
    assert classify(79) == "growth"
    assert classify(80) == "aggressive"


def test_sample_answers_score_balanced() -> None:
    answers = {
        "horizon_years": 8,
        "age": 36,
        "drawdown_tolerance": "medium",
        "income_stability": "stable",
        "emergency_months": 3,
        "liquidity_needs": "high",
    }
    assert risk_score(answers) == 54
    assert build_profile(answers).name == "balanced"
    assert run_questionnaire(answers).score == 54
