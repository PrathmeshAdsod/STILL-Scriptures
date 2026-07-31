from fastapi.testclient import TestClient

from app.main import app


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
