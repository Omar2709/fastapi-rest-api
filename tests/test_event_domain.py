from app.domain.events import EventType


def test_event_type_values_are_stable() -> None:
    assert {event_type.value for event_type in EventType} == {
        "job.submitted",
    }
