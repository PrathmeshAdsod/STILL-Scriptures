from uuid import uuid4

import pytest

from app.repositories import AnalysisReservationResult, InMemoryDataStore


@pytest.mark.asyncio
async def test_analysis_reservations_are_idempotent_and_bounded() -> None:
    store = InMemoryDataStore()
    first = uuid4()
    assert await store.reserve_analysis(owner_id="one", project_id=first, per_user_limit=1, global_limit=2) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="one", project_id=first, per_user_limit=1, global_limit=2) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="one", project_id=uuid4(), per_user_limit=1, global_limit=2) == AnalysisReservationResult.USER_LIMIT_REACHED
    assert await store.reserve_analysis(owner_id="two", project_id=uuid4(), per_user_limit=1, global_limit=2) == AnalysisReservationResult.RESERVED
    assert await store.reserve_analysis(owner_id="three", project_id=uuid4(), per_user_limit=1, global_limit=2) == AnalysisReservationResult.GLOBAL_LIMIT_REACHED
