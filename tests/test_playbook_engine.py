from pathlib import Path

import pytest

from app.claims.claim_state import ClaimState
from app.claims.playbook_engine import PlaybookEngine


PLAYBOOK = Path("app/claims/playbook.yaml")


@pytest.fixture
def engine() -> PlaybookEngine:
    return PlaybookEngine.from_yaml(PLAYBOOK)


def test_first_stage_is_opening_situation(engine: PlaybookEngine) -> None:
    claim = ClaimState(session_id="claim_test")

    assert engine.current_stage(claim) == "opening_situation"
    assert list(engine.get_missing_fields(claim).keys()) == ["incident.description"]


def test_safety_check_runs_after_opening_situation(engine: PlaybookEngine) -> None:
    claim = ClaimState(session_id="claim_test")

    claim.merge_update({"incident.description": "Rear-end collision"})

    assert engine.current_stage(claim) == "safety_check"
    assert list(engine.get_missing_fields(claim).keys()) == ["safety.is_safe_location"]


def test_safe_caller_skips_unsafe_branch_into_identification(engine: PlaybookEngine) -> None:
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": True,
        }
    )

    assert engine.current_stage(claim) == "identification"


def test_unsafe_caller_pauses_intake_until_emergency_dispatched(engine: PlaybookEngine) -> None:
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": False,
        }
    )

    assert engine.current_stage(claim) == "unsafe_handling"

    claim.merge_update({"safety.needs_assistance": True})
    assert engine.current_stage(claim) == "emergency_dispatch"

    claim.merge_update({"safety.emergency_services_dispatched": True})
    assert engine.current_stage(claim) == "identification"


def test_unsafe_caller_refusing_assistance_skips_emergency_dispatch(
    engine: PlaybookEngine,
) -> None:
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": False,
            "safety.needs_assistance": False,
        }
    )

    assert engine.current_stage(claim) == "identification"


def test_safety_branch_resumes_when_caller_becomes_unsafe_again(
    engine: PlaybookEngine,
) -> None:
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": True,
            "caller.is_policyholder": True,
            "caller.full_name": "Alex Rider",
            "policyholder.policy_number": "POL-1",
        }
    )
    assert engine.current_stage(claim) == "policyholder_dob"

    claim.merge_update({"safety.is_safe_location": False})
    assert engine.current_stage(claim) == "unsafe_handling"


def test_no_human_handoff_stage_in_playbook(engine: PlaybookEngine) -> None:
    assert "escalate" not in engine.states
    assert "escalate" not in engine.ordered_state_names

    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": False,
            "safety.needs_assistance": True,
        }
    )

    assert engine.current_stage(claim) == "emergency_dispatch"


def test_non_policyholder_caller_branch_collects_relationship(engine: PlaybookEngine) -> None:
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": True,
            "caller.is_policyholder": False,
            "caller.full_name": "Sam Caller",
        }
    )

    assert engine.current_stage(claim) == "caller_relationship"
    missing = list(engine.get_missing_fields(claim).keys())
    assert "caller.relationship_to_policyholder" in missing
    assert "policyholder.full_name" in missing


def test_unknown_marker_lets_engine_advance(engine: PlaybookEngine) -> None:
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": True,
            "caller.is_policyholder": True,
            "caller.full_name": "Alex Rider",
            "policyholder.policy_number": "unknown",
            "policyholder.full_name": "Alex Rider",
            "policyholder.date_of_birth": "unknown",
        }
    )

    assert engine.current_stage(claim) == "incident_details"


def test_nested_and_dot_notation_updates_overwrite_values() -> None:
    claim = ClaimState(session_id="claim_test")

    claim.merge_update({"caller": {"full_name": "Jones"}})
    claim.merge_update({"caller.full_name": "Smith"})

    assert claim.caller.full_name == "Smith"


def test_damage_items_string_is_normalized_to_list() -> None:
    claim = ClaimState(session_id="claim_test")

    claim.merge_update({"damage.items": "bumper, trunk"})

    assert claim.damage.items == ["bumper", "trunk"]


def test_non_policyholder_unknown_policy_uses_alternate_identifier(
    engine: PlaybookEngine,
) -> None:
    """Non-policyholder caller without policy number uses alternate identifier and continues."""
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": True,
            "caller.is_policyholder": False,
            "caller.full_name": "Sam Caller",
            "caller.relationship_to_policyholder": "spouse",
            "policyholder.full_name": "Pat Policyholder",
        }
    )

    assert engine.current_stage(claim) == "policyholder_details"

    claim.merge_update(
        {
            "policyholder.policy_number": "unknown",
            "policyholder.alternate_identifier": "1980-03-14",
        }
    )

    assert engine.current_stage(claim) == "incident_details"


def test_phone_collection_required_at_end(engine: PlaybookEngine) -> None:
    """Phone number is asked near the end of the call, not during identification."""
    fields = engine.all_required_fields()
    assert "caller.phone_number" in fields
    incident_idx = fields.index("incident.description")
    phone_idx = fields.index("caller.phone_number")
    assert phone_idx > incident_idx


def test_phone_collection_accepts_unknown_marker(engine: PlaybookEngine) -> None:
    """If caller refuses phone number, marking 'unknown' should advance to done."""
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Rear-end collision",
            "safety.is_safe_location": True,
            "caller.is_policyholder": True,
            "caller.full_name": "Mark Stevens",
            "policyholder.full_name": "Mark Stevens",
            "policyholder.date_of_birth": "1980-03-14",
            "policyholder.policy_number": "POL-1",
            "claim_type": "auto accident",
            "incident.date": "2026-04-20",
            "incident.location": "Berlin",
            "incident.time": "09:00",
            "incident.road_type": "urban street",
            "incident.weather": "clear",
            "driver.policyholder_was_driving": True,
            "driver.hit_and_run": False,
            "third_parties.involved": False,
            "safety.injuries": False,
            "safety.police_report": False,
            "damage.items": ["rear bumper"],
            "damage.description": "Scratched rear bumper",
            "damage.estimated_value": "unknown",
            "damage.photos_available": True,
            "services.rental_car_needed": False,
            "services.repair_shop_selected": False,
            "documents.photos": True,
            "documents.receipts": False,
            "documents.police_report": False,
        }
    )
    assert engine.current_stage(claim) == "phone_collection"

    claim.merge_update({"caller.phone_number": "unknown"})
    assert engine.current_stage(claim) == "done"


def test_or_skip_condition_supported(engine: PlaybookEngine) -> None:
    """The engine evaluates `||` between simple equality conditions."""
    claim = ClaimState(session_id="claim_test")
    claim.merge_update(
        {
            "incident.description": "Crash",
            "safety.is_safe_location": True,
        }
    )
    state = engine.states["emergency_dispatch"]
    assert engine._eval_skip_if(claim, state.skip_if) is True

    claim.merge_update({"safety.is_safe_location": False, "safety.needs_assistance": False})
    assert engine._eval_skip_if(claim, state.skip_if) is True

    claim.merge_update({"safety.is_safe_location": False, "safety.needs_assistance": True})
    assert engine._eval_skip_if(claim, state.skip_if) is False


def test_state_lacks_handoff_or_risk_flags_legacy_fields() -> None:
    """Legacy escalation fields must not exist on the new ClaimState."""
    claim = ClaimState(session_id="claim_test")
    assert not hasattr(claim, "handoff_required")
    assert not hasattr(claim, "risk_flags")
    assert hasattr(claim, "disposition")
