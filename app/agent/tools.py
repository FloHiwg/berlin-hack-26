from __future__ import annotations

from pathlib import Path
from typing import Any

from app.claims.claim_state import ClaimState
from app.claims.playbook_engine import PlaybookEngine


class SessionFinished(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ClaimToolHandlers:
    def __init__(
        self,
        claim_state: ClaimState,
        playbook_engine: PlaybookEngine,
        storage_dir: Path,
    ) -> None:
        self.claim_state = claim_state
        self.playbook_engine = playbook_engine
        self.storage_dir = storage_dir
        self.finished_reason: str | None = None

    def update_claim_state(self, claim_update: dict[str, Any]) -> dict[str, Any]:
        invalid_fields = self.claim_state.merge_update(claim_update)
        self.claim_state.save(self.storage_dir)
        result = self._status("updated")
        if invalid_fields:
            result["ignored_fields"] = invalid_fields
            result["status"] = "updated_with_ignored_fields"
        return result

    def escalate(self, reason: str, risk_flags: list[str]) -> dict[str, Any]:
        self.claim_state.handoff_required = True
        for flag in risk_flags:
            if flag not in self.claim_state.risk_flags:
                self.claim_state.risk_flags.append(flag)
        self.claim_state.mark_completed()
        self.claim_state.save(self.storage_dir)
        print(
            "\nESCALATION: A human claims specialist is required."
            f"\nReason: {reason}\n",
            flush=True,
        )
        self.finished_reason = "escalated"
        return self._status("escalated")

    def finalize_claim(self) -> dict[str, Any]:
        missing = self.playbook_engine.get_missing_fields(self.claim_state)
        if missing:
            return self._status("missing_required_fields")
        self.claim_state.mark_completed()
        self.claim_state.save(self.storage_dir)
        self.finished_reason = "finalized"
        return self._status("finalized")

    def dispatch(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "update_claim_state":
            return self.update_claim_state(args.get("claim_update", {}))
        if name == "escalate":
            return self.escalate(
                reason=args.get("reason", "Escalation requested"),
                risk_flags=list(args.get("risk_flags", [])),
            )
        if name == "finalize_claim":
            return self.finalize_claim()
        return {"status": "unknown_tool", "tool_name": name}

    def _status(self, status: str) -> dict[str, Any]:
        return {
            "status": status,
            "missing_fields": self.playbook_engine.get_missing_fields(self.claim_state),
            "current_stage": self.playbook_engine.current_stage(self.claim_state),
        }
