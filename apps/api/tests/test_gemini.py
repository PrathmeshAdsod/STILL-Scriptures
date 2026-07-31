from app.providers.gemini import GeminiVideoProvider
from app.schemas import NarrativeState


def test_gemini_state_normalization_preserves_prior_prefix_and_appends_new_items() -> None:
    previous = NarrativeState(
        version=1,
        revealed_facts=["A person enters the room."],
        observed_events=["The door opens."],
        content_mode="documentary",
    )
    proposed = NarrativeState(
        version=2,
        revealed_facts=["The person entered.", "A second person responds."],
        observed_events=["A reply is heard.", "The door opens."],
        content_mode="drama",
    )

    normalized = GeminiVideoProvider._normalize_append_only_state(previous=previous, proposed=proposed)

    assert normalized.version == 2
    assert normalized.revealed_facts == [
        "A person enters the room.",
        "The person entered.",
        "A second person responds.",
    ]
    assert normalized.observed_events == ["The door opens.", "A reply is heard."]
    assert normalized.content_mode == "documentary"
