from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.claims.claim_state import ClaimState, is_filled


@dataclass(frozen=True)
class PlaybookState:
    name: str
    required: list[str]
    next: str | None


class PlaybookEngine:
    def __init__(self, states: dict[str, PlaybookState]) -> None:
        self.states = states
        self.ordered_state_names = [
            name for name in states if name not in {"escalate", "done"}
        ]

    @classmethod
    def from_yaml(cls, path: Path) -> "PlaybookEngine":
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        states: dict[str, PlaybookState] = {}
        for name, config in raw["states"].items():
            states[name] = PlaybookState(
                name=name,
                required=list(config.get("required", [])),
                next=config.get("next"),
            )
        return cls(states)

    def current_stage(self, claim_state: ClaimState) -> str:
        if claim_state.handoff_required or claim_state.safety.urgent_risk is True:
            return "escalate"

        stage_name = self.ordered_state_names[0]
        seen: set[str] = set()
        while stage_name not in seen:
            seen.add(stage_name)
            state = self.states[stage_name]
            if self._missing_for_state(claim_state, state):
                return stage_name
            if not state.next or state.next == "done":
                return "done"
            stage_name = state.next
        raise ValueError("Playbook contains a cycle")

    def get_missing_fields(self, claim_state: ClaimState) -> list[str]:
        stage = self.current_stage(claim_state)
        if stage in {"done", "escalate"}:
            return []
        return self._missing_for_state(claim_state, self.states[stage])

    def all_required_fields(self) -> list[str]:
        fields: list[str] = []
        for state_name in self.ordered_state_names:
            fields.extend(self.states[state_name].required)
        return fields

    def _missing_for_state(
        self, claim_state: ClaimState, state: PlaybookState
    ) -> list[str]:
        missing: list[str] = []
        for field_path in state.required:
            value: Any = claim_state.get_path(field_path)
            if not is_filled(value):
                missing.append(field_path)
        return missing
