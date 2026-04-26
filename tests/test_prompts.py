from pathlib import Path

import pytest

from app.agent.prompts import (
    EMERGENCY_DISPATCH_PHRASE,
    EXACT_OPENING,
    NEXT_STEPS_SCRIPT,
    build_system_prompt,
)
from app.claims.claim_state import ClaimState
from app.claims.playbook_engine import PlaybookEngine


@pytest.fixture
def engine() -> PlaybookEngine:
    return PlaybookEngine.from_yaml(Path("app/claims/playbook.yaml"))


def _prompt(engine: PlaybookEngine, **kwargs) -> str:
    return build_system_prompt(engine, ClaimState(session_id="claim_test"), **kwargs)


def test_prompt_includes_exact_opening_line(engine: PlaybookEngine) -> None:
    assert EXACT_OPENING == (
        "Hello, this is Lisa from National Insurance emergency hotline. What happened?"
    )
    assert EXACT_OPENING in _prompt(engine)


def test_prompt_includes_fixed_emergency_dispatch_phrase(engine: PlaybookEngine) -> None:
    assert (
        EMERGENCY_DISPATCH_PHRASE
        == "Emergency services have been dispatched to your location."
    )
    assert EMERGENCY_DISPATCH_PHRASE in _prompt(engine)


def test_prompt_includes_fixed_next_steps_script(engine: PlaybookEngine) -> None:
    assert NEXT_STEPS_SCRIPT in _prompt(engine)


def test_prompt_states_no_human_handoff(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "do NOT transfer to a human" in prompt.lower() or "no human handoff" in prompt.lower()


def test_prompt_uses_caller_and_policyholder_field_names(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "caller.full_name" in prompt
    assert "caller.is_policyholder" in prompt
    assert "policyholder.policy_number" in prompt
    assert "policyholder.alternate_identifier" in prompt
    assert "customer.full_name" not in prompt


def test_prompt_describes_unknown_handling(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "'unknown'" in prompt
    assert "do not repeatedly re-ask" in prompt.lower()


def test_prompt_describes_one_question_at_a_time(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "ONE question at a time" in prompt or "one question at a time" in prompt.lower()


def test_prompt_describes_phone_number_at_end(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "near the END of the call" in prompt or "near the end of the call" in prompt.lower()


def test_prompt_describes_no_recap_before_close(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "do not recap" in prompt.lower() or "do NOT recap" in prompt


def test_prompt_describes_legal_question_redirect(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "legal-interpretation" in prompt.lower() or "fault" in prompt.lower()


def test_prompt_describes_abuse_warning_then_end(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine)
    assert "abusive" in prompt.lower()
    assert "abuse_terminated" in prompt


def test_voice_mode_first_call_demands_exact_opening(engine: PlaybookEngine) -> None:
    prompt = _prompt(engine, voice_mode=True)
    assert "EXACT opening" in prompt
    assert EXACT_OPENING in prompt
