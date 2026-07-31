from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.auth import require_cloud_task
from app.config import Settings


@pytest.mark.asyncio
async def test_production_worker_rejects_a_spoofed_task_header_without_oidc() -> None:
    settings = Settings(
        app_mode="production",
        youtube_api_key="restricted-key",
        gloo_max_candidates_per_project=1,
        worker_base_url="https://still-api.example",
        worker_invoker_service_account="still-task@example.iam.gserviceaccount.com",
    )
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings)))
    with pytest.raises(HTTPException) as error:
        await require_cloud_task(request, authorization=None, task_name="projects/p/locations/l/queues/q/tasks/t")
    assert error.value.status_code == 403
