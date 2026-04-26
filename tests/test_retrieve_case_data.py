"""Tests for the retrieve_case_data tool implementation."""
import tempfile
from pathlib import Path

import pytest

from app.agent.tools import ClaimToolHandlers
from app.claims.case_database import (
    retrieve_case_by_claim_id,
    retrieve_case_by_phone,
    format_case_response,
)
from app.claims.claim_state import ClaimState
from app.claims.playbook_engine import PlaybookEngine


@pytest.fixture
def playbook_engine():
    """Load the playbook for testing."""
    playbook_path = Path("app/claims/playbook.yaml")
    return PlaybookEngine.from_yaml(playbook_path)


def test_retrieve_case_by_phone():
    case = retrieve_case_by_phone("+49301234567")
    assert case is not None
    assert case["case_id"] == "CLM-2024-001"
    assert case["claimant_full_name"] == "Anna Mueller"
    assert case["claim_type"] == "car_accident"


def test_retrieve_case_by_claim_id():
    case = retrieve_case_by_claim_id("CLM-2024-001")
    assert case is not None
    assert case["claimant_full_name"] == "Anna Mueller"


def test_retrieve_nonexistent_case():
    case = retrieve_case_by_phone("+49999999999")
    assert case is None


def test_format_case_response_found():
    case = retrieve_case_by_phone("+49301234567")
    response = format_case_response(case)
    assert response["status"] == "found"
    assert response["claimant_name"] == "Anna Mueller"


def test_format_case_response_not_found():
    response = format_case_response(None)
    assert response["status"] == "not_found"


def test_retrieve_case_data_tool_populates_policyholder_fields(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)

        claim_state = ClaimState(session_id="test_retrieve")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.retrieve_case_data(phone_number="+49301234567")

        assert result["status"] == "found"
        assert claim_state.policyholder.full_name == "Anna Mueller"
        assert claim_state.policyholder.policy_number == "POL-2023-4567"
        assert claim_state.claim_type == "car_accident"
        assert claim_state.incident.date == "2024-04-20"
        assert claim_state.incident.location == "Berlin, Kreuzberg"
        assert claim_state.third_parties.involved is True


def test_retrieve_case_data_tool_via_dispatch(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_dispatch")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.dispatch(
            "retrieve_case_data", {"phone_number": "+49307654321"}
        )

        assert result["status"] == "found"
        assert claim_state.policyholder.full_name == "Marcus Weber"
        assert claim_state.claim_type == "home_damage"


def test_end_call_marks_session_finished_without_handoff(playbook_engine):
    """end_call records disposition and ends the session; it must NOT request handoff."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_end_call")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.dispatch(
            "end_call",
            {
                "reason": "Caller in unsafe location, no assistance needed",
                "disposition": "unsafe_callback",
            },
        )

        assert result["status"] == "ended"
        assert handlers.finished_reason == "ended"
        assert claim_state.disposition == "unsafe_callback"
        assert claim_state.completed_at is not None
        assert not hasattr(claim_state, "handoff_required") or getattr(
            claim_state, "handoff_required", False
        ) is False


def test_end_call_without_disposition_still_ends(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_end_minimal")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.dispatch("end_call", {"reason": "Caller asked to stop"})

        assert result["status"] == "ended"
        assert handlers.finished_reason == "ended"
        assert claim_state.disposition is None


def test_finalize_claim_does_not_end_call(playbook_engine):
    """finalize_claim completes the claim but leaves room for goodbye + end_call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)

        claim_state = ClaimState(session_id="test_finalize")
        claim_state.merge_update(
            {
                "incident.description": "Rear-end collision",
                "safety.is_safe_location": True,
                "caller.is_policyholder": True,
                "caller.full_name": "Mark Stevens",
                "caller.phone_number": "unknown",
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
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.dispatch("finalize_claim", {})

        assert result["status"] == "finalized"
        assert handlers.finished_reason is None
        assert claim_state.completed_at is not None


def test_update_case_status_valid(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_status")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.update_case_status("assessment_in_progress")

        assert result["status"] == "updated"
        assert result["new_status"] == "assessment_in_progress"
        assert claim_state.status == "assessment_in_progress"


def test_update_case_status_invalid(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_invalid_status")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.update_case_status("invalid_status_xyz")

        assert result["status"] == "invalid_status"
        assert claim_state.status is None


def test_update_case_status_via_dispatch(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_dispatch_status")
        claim_state.status = "pending_details"
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.dispatch(
            "update_case_status", {"new_status": "documentation_required"}
        )

        assert result["status"] == "updated"
        assert claim_state.status == "documentation_required"


def test_update_case_status_case_insensitive(playbook_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        claim_state = ClaimState(session_id="test_case_insensitive")
        handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

        result = handlers.update_case_status("APPROVED")

        assert result["status"] == "updated"
        assert claim_state.status == "approved"
