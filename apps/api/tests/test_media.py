from app.media import plan_semantic_windows


def test_semantic_windows_cover_duration_without_future_interval() -> None:
    windows = plan_semantic_windows(95, base_seconds=40)
    assert [(item.start_seconds, item.end_seconds) for item in windows] == [(0.0, 40.0), (40.0, 80.0), (80.0, 95)]
    assert all(window.end_seconds >= window.start_seconds for window in windows)
