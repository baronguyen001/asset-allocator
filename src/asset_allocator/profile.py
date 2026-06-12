"""Questionnaire scoring for illustrative allocation defaults.

NOT FINANCIAL ADVICE. The questionnaire maps user-supplied answers to illustrative,
user-tunable model defaults. It does not recommend securities or decide what anyone
should buy, sell, or hold.
"""

from __future__ import annotations

from typing import cast

from asset_allocator.models import RiskProfile

QUESTIONS: list[dict[str, object]] = [
    {
        "key": "horizon_years",
        "prompt": "Investment horizon in years",
        "type": "int",
        "choices": [],
    },
    {"key": "age", "prompt": "Age, or blank if not used", "type": "optional_int", "choices": []},
    {
        "key": "drawdown_tolerance",
        "prompt": "Largest short-term drawdown you could tolerate",
        "type": "choice",
        "choices": [("low", 5), ("medium", 14), ("high", 24)],
    },
    {
        "key": "income_stability",
        "prompt": "Income stability",
        "type": "choice",
        "choices": [("unstable", 4), ("stable", 11), ("very_stable", 17)],
    },
    {
        "key": "emergency_months",
        "prompt": "Emergency-fund months already available",
        "type": "int",
        "choices": [],
    },
    {
        "key": "liquidity_needs",
        "prompt": "Expected near-term liquidity needs",
        "type": "choice",
        "choices": [("high", 4), ("medium", 10), ("low", 16)],
    },
]


def _choice_points(question_key: str, value: object) -> int:
    question = next(q for q in QUESTIONS if q["key"] == question_key)
    choices = cast(list[tuple[str, int]], question["choices"])
    mapping = {label: points for label, points in choices}
    return int(mapping.get(str(value), 0))


def _to_int(value: object, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(str(value))


def risk_score(answers: dict[str, object]) -> int:
    horizon = max(0, _to_int(answers.get("horizon_years", 0)))
    horizon_points = min(25, horizon * 2)
    drawdown_points = _choice_points("drawdown_tolerance", answers.get("drawdown_tolerance"))
    income_points = _choice_points("income_stability", answers.get("income_stability"))
    emergency = max(0, _to_int(answers.get("emergency_months", 0)))
    emergency_points = min(18, emergency * 3)
    liquidity_points = _choice_points("liquidity_needs", answers.get("liquidity_needs"))
    score = horizon_points + drawdown_points + income_points + emergency_points + liquidity_points
    return max(0, min(100, int(score)))


def classify(score: int) -> str:
    if score < 35:
        return "conservative"
    if score < 60:
        return "balanced"
    if score < 80:
        return "growth"
    return "aggressive"


def build_profile(answers: dict[str, object]) -> RiskProfile:
    score = risk_score(answers)
    raw_age = answers.get("age")
    age = None if raw_age in (None, "") else _to_int(raw_age)
    notes = str(answers.get("notes", ""))
    return RiskProfile(
        name=classify(score),
        score=score,
        horizon_years=_to_int(answers.get("horizon_years", 0)),
        age=age,
        notes=notes,
    )


def run_questionnaire(answers: dict[str, object] | None = None) -> RiskProfile:
    if answers is not None:
        return build_profile(answers)
    collected: dict[str, object] = {}
    for question in QUESTIONS:
        key = str(question["key"])
        prompt = str(question["prompt"])
        qtype = str(question["type"])
        choices = cast(list[tuple[str, int]], question["choices"])
        if choices:
            labels = ", ".join(str(label) for label, _ in choices)
            prompt = f"{prompt} ({labels})"
        raw = input(f"{prompt}: ").strip()
        if qtype == "int":
            collected[key] = int(raw)
        elif qtype == "optional_int":
            collected[key] = None if raw == "" else int(raw)
        else:
            collected[key] = raw
    return build_profile(collected)
