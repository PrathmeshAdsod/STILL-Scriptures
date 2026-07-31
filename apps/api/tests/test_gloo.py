from app.config import Settings
from app.providers.gloo import GlooSacredTimingProvider


def _tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "record_decision",
            "parameters": {"type": "object", "properties": {}},
        },
    }


def test_gloo_auto_routing_omits_tradition_for_general_perspective() -> None:
    provider = GlooSacredTimingProvider(Settings(gloo_endpoint_mode="completions_v2"))

    payload = provider._build_request_payload(system="system", user_payload={"value": 1}, tool=_tool())

    assert payload["auto_routing"] is True
    assert "tradition" not in payload
    assert "model" not in payload
    assert "model_family" not in payload


def test_gloo_auto_routing_includes_supported_explicit_tradition() -> None:
    provider = GlooSacredTimingProvider(
        Settings(gloo_endpoint_mode="completions_v2", gloo_tradition="evangelical")
    )

    payload = provider._build_request_payload(system="system", user_payload={}, tool=_tool())

    assert payload["tradition"] == "evangelical"
