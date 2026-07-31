from __future__ import annotations

import asyncio
from typing import Protocol
from uuid import UUID

from .config import Settings
from .worker import CausalAnalysisWorker


class TaskEnqueuer(Protocol):
    async def enqueue_analysis(self, job_id: UUID) -> None: ...


class LocalTaskEnqueuer:
    def __init__(self, worker: CausalAnalysisWorker, enabled: bool) -> None:
        self.worker = worker
        self.enabled = enabled

    async def enqueue_analysis(self, job_id: UUID) -> None:
        if self.enabled:
            asyncio.create_task(self.worker.run(job_id))


class CloudTasksEnqueuer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def enqueue_analysis(self, job_id: UUID) -> None:
        if not all((self.settings.google_cloud_project, self.settings.cloud_tasks_queue, self.settings.worker_base_url, self.settings.worker_invoker_service_account)):
            raise RuntimeError("Cloud Tasks configuration is incomplete.")
        await asyncio.to_thread(self._enqueue_sync, job_id)

    def _enqueue_sync(self, job_id: UUID) -> None:
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(self.settings.google_cloud_project, self.settings.google_cloud_location, self.settings.cloud_tasks_queue)
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.settings.worker_base_url.rstrip('/')}/internal/jobs/{job_id}",
                "oidc_token": {"service_account_email": self.settings.worker_invoker_service_account},
            }
        }
        client.create_task(parent=parent, task=task)
