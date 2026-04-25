from pathlib import Path

from app.claims.claim_state import ClaimState
from app.claims.playbook_engine import PlaybookEngine


PLAYBOOK = Path("app/claims/playbook.yaml")


def test_stage_advances_as_required_fields_are_filled() -> None:
    engine = PlaybookEngine.from_yaml(PLAYBOOK)
    claim = ClaimState(session_id="claim_test")

    assert engine.current_stage(claim) == "identify_customer"
    assert engine.get_missing_fields(claim) == [
        "customer.full_name",
        "customer.policy_number",
        "customer.date_of_birth",
    ]

    claim.merge_update(
        {
            "customer.full_name": "Maya Smith",
            "customer.policy_number": "POL-123",
            "customer.date_of_birth": "1990-01-02",
        }
    )

    assert engine.current_stage(claim) == "classify_claim"


def test_escalation_stage_wins_over_progression() -> None:
    engine = PlaybookEngine.from_yaml(PLAYBOOK)
    claim = ClaimState(session_id="claim_test")

    claim.merge_update({"safety.urgent_risk": True})

    assert engine.current_stage(claim) == "escalate"
    assert engine.get_missing_fields(claim) == []


def test_nested_and_dot_notation_updates_overwrite_values() -> None:
    claim = ClaimState(session_id="claim_test")

    claim.merge_update({"customer": {"full_name": "Jones"}})
    claim.merge_update({"customer.full_name": "Smith"})

    assert claim.customer.full_name == "Smith"


def test_damage_items_string_is_normalized_to_list() -> None:
    claim = ClaimState(session_id="claim_test")

    claim.merge_update({"damage.items": "bumper, trunk"})

    assert claim.damage.items == ["bumper", "trunk"]
