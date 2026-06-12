from __future__ import annotations

from datetime import UTC, datetime

import pytest

from asset_allocator.models import TargetAllocation


@pytest.fixture
def as_of() -> str:
    return datetime(2026, 6, 12, tzinfo=UTC).isoformat()


@pytest.fixture
def balanced_target() -> TargetAllocation:
    return TargetAllocation(
        profile_name="balanced",
        weights={
            "equity": 40,
            "bonds": 25,
            "gold": 10,
            "real_estate": 10,
            "savings": 8,
            "cash": 4,
            "emergency": 3,
        },
    )
