import asyncio
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ProjectStatus


def test_analysis_start_is_idempotent_and_owned() -> None:
    headers = {"X-Development-User": "owner"}
    with TestClient(app) as client:
        created = client.post("/api/projects", headers=headers, json={"title": "A story"})
        assert created.status_code == 201
        project_id = created.json()["project_id"]
        completed = client.post(
            f"/api/projects/{project_id}/source/upload-complete",
            headers=headers,
            json={
                "storage_path": f"gs://bucket/projects/{project_id}/sources/source.mp4",
                "original_filename": "source.mp4",
                "content_type": "video/mp4",
                "size_bytes": 1024,
                "sha256": "a" * 64,
                "duration_seconds": 60,
                "has_video": True,
            },
        )
        assert completed.status_code == 200
        first = client.post(f"/api/projects/{project_id}/analysis", headers={**headers, "Idempotency-Key": "stable-key"})
        second = client.post(f"/api/projects/{project_id}/analysis", headers={**headers, "Idempotency-Key": "stable-key"})
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        forbidden = client.get(f"/api/projects/{project_id}", headers={"X-Development-User": "other"})
        assert forbidden.status_code == 403


def test_saved_video_library_lookup_and_session_resume_are_owned() -> None:
    owner = {"X-Development-User": "library-owner"}
    other = {"X-Development-User": "other-owner"}
    video_url = "https://youtu.be/07d2dXHYb94"
    with TestClient(app) as client:
        created = client.post("/api/projects", headers=owner, json={"title": "A saved story"})
        project_id = created.json()["project_id"]
        source = client.post(
            f"/api/projects/{project_id}/source/youtube",
            headers=owner,
            json={"url": video_url, "title": "A saved story", "duration_seconds": 245},
        )
        assert source.status_code == 200
        assert source.json()["source"]["youtube_video_id"] == "07d2dXHYb94"

        own_library = client.get("/api/projects", headers=owner)
        assert own_library.status_code == 200
        assert [item["project"]["id"] for item in own_library.json()] == [project_id]
        assert client.get("/api/projects", headers=other).json() == []

        lookup = client.get("/api/projects/lookup/youtube", headers=owner, params={"url": video_url})
        assert lookup.status_code == 200
        assert lookup.json()["project"]["id"] == project_id
        assert client.get("/api/projects/lookup/youtube", headers=other, params={"url": video_url}).json() is None

        store = client.app.state.store
        project = asyncio.run(store.get_project(UUID(project_id)))
        project.status = ProjectStatus.READY
        asyncio.run(store.put_project(project))

        first = client.post(f"/api/projects/{project_id}/viewing-sessions/resume", headers=owner)
        assert first.status_code == 200
        session_id = first.json()["id"]
        saved = client.patch(
            f"/api/projects/{project_id}/viewing-sessions/{session_id}",
            headers=owner,
            json={"ranges": [[0, 18]], "duration_seconds": 245, "ended_naturally": False},
        )
        assert saved.status_code == 200
        assert saved.json()["contiguous_frontier_seconds"] == 18
        resumed = client.post(f"/api/projects/{project_id}/viewing-sessions/resume", headers=owner)
        assert resumed.json()["id"] == session_id
        assert resumed.json()["contiguous_frontier_seconds"] == 18

        assert client.delete(f"/api/projects/{project_id}", headers=other).status_code == 403
        assert client.delete(f"/api/projects/{project_id}", headers=owner).status_code == 204
        assert client.get("/api/projects", headers=owner).json() == []


def test_account_deletion_removes_all_owned_application_data() -> None:
    headers = {"X-Development-User": "delete-owner"}
    with TestClient(app) as client:
        first = client.post("/api/projects", headers=headers, json={"title": "First"})
        second = client.post("/api/projects", headers=headers, json={"title": "Second"})
        assert first.status_code == second.status_code == 201
        assert len(client.get("/api/projects", headers=headers).json()) == 2
        deleted = client.delete("/api/account", headers=headers)
        assert deleted.status_code == 204
        assert client.get("/api/projects", headers=headers).json() == []


def test_viewing_session_cannot_unlock_a_different_project() -> None:
    headers = {"X-Development-User": "frontier-owner"}
    with TestClient(app) as client:
        first_id = client.post("/api/projects", headers=headers, json={"title": "First"}).json()["project_id"]
        second_id = client.post("/api/projects", headers=headers, json={"title": "Second"}).json()["project_id"]
        store = client.app.state.store
        for project_id in (first_id, second_id):
            project = asyncio.run(store.get_project(UUID(project_id)))
            project.status = ProjectStatus.READY
            asyncio.run(store.put_project(project))
        session = client.post(f"/api/projects/{first_id}/viewing-sessions/resume", headers=headers).json()

        echoes = client.get(f"/api/projects/{second_id}/echoes", headers=headers, params={"session_id": session["id"]})
        reflection = client.post(f"/api/projects/{second_id}/story-reflection", headers=headers, params={"session_id": session["id"]})

        assert echoes.status_code == 404
        assert reflection.status_code == 409
