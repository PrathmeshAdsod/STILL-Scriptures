from uuid import uuid4

import pytest

from app.repositories import AnalysisReservationResult, InMemoryDataStore


@pytest.mark.asyncio
async def test_analysis_reservations_are_idempotent_and_bounded() -> None:
    store = InMemoryDataStore()
    first = uuid4()
    limits = {"free_limit": 1, "access_daily_limit": 2, "global_limit": 3}
    assert await store.reserve_analysis(owner_id="one", project_id=first, **limits) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="one", project_id=first, **limits) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="one", project_id=uuid4(), **limits) == AnalysisReservationResult.USER_LIMIT_REACHED
    await store.grant_access(owner_id="two")
    assert await store.reserve_analysis(owner_id="two", project_id=uuid4(), **limits) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="two", project_id=uuid4(), **limits) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="two", project_id=uuid4(), **limits) == AnalysisReservationResult.USER_LIMIT_REACHED
    assert await store.reserve_analysis(owner_id="three", project_id=uuid4(), **limits) == AnalysisReservationResult.GLOBAL_LIMIT_REACHED


@pytest.mark.asyncio
async def test_account_status_changes_after_access_code_grant() -> None:
    store = InMemoryDataStore()
    free = await store.account_status(owner_id="account", free_limit=1, access_daily_limit=2, max_duration_seconds=360)
    assert free.plan == "FREE"
    assert free.analyses_remaining == 1
    assert free.usage_period == "lifetime"
    await store.grant_access(owner_id="account")
    access = await store.account_status(owner_id="account", free_limit=1, access_daily_limit=2, max_duration_seconds=360)
    assert access.plan == "ACCESS"
    assert access.analyses_remaining == 2
    assert access.usage_period == "day"
