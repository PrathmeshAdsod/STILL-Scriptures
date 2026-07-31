from app.config import Settings
from app.providers.gloo import GlooSacredTimingProvider, PASSAGE_VERIFICATION_SYSTEM, SACRED_TIMING_SYSTEM


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


def test_sacred_timing_rejects_shaming_and_superficial_wordplay() -> None:
    decision_policy = SACRED_TIMING_SYSTEM.lower()
    verification_policy = PASSAGE_VERIFICATION_SYSTEM.lower()

    assert "ordinary leisure" in decision_policy
    assert "superficial wordplay" in decision_policy
    assert "severe moral label" in verification_policy
    assert "must disclaim" in verification_policy
