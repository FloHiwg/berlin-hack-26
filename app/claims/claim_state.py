from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


METADATA_FIELDS: frozenset[str] = frozenset(
    {"session_id", "created_at", "completed_at", "status", "disposition"}
)


class Caller(BaseModel):
    """The person actually on the phone with Lisa."""

    is_policyholder: bool | None = None
    full_name: str | None = None
    relationship_to_policyholder: str | None = None
    phone_number: str | None = None


class CustomerProfile(BaseModel):
    """Customer profile information fetched when policy number is identified."""

    membership_since: str | None = None  # ISO date format
    # Future extensibility: tier, total_claims, etc.


class Policyholder(BaseModel):
    """The insured person whose policy the claim is filed against."""

    full_name: str | None = None
    date_of_birth: str | None = None
    policy_number: str | None = None
    alternate_identifier: str | None = None
    customer_profile: CustomerProfile = Field(default_factory=CustomerProfile)


class Incident(BaseModel):
    date: str | None = None
    date_is_approximate: bool | None = None
    time: str | None = None
    time_is_approximate: bool | None = None
    location: str | None = None
    description: str | None = None
    road_type: str | None = None
    weather: str | None = None


class Driver(BaseModel):
    policyholder_was_driving: bool | None = None
    license_valid: bool | None = None
    listed_under_policy: bool | None = None
    impairment_involved: bool | None = None
    hit_and_run: bool | None = None


class Damage(BaseModel):
    items: list[str] = Field(default_factory=list)
    description: str | None = None
    estimated_value: str | int | float | None = None
    photos_available: bool | None = None

    @field_validator("items", mode="before")
    @classmethod
    def coerce_items(cls, v: object) -> object:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


class ThirdParties(BaseModel):
    involved: bool | None = None
    details: str | None = None
    witness_info: str | None = None


class Services(BaseModel):
    rental_car_needed: bool | None = None
    rental_car_preference: str | None = None
    repair_shop_selected: bool | None = None
    repair_shop_preference: str | None = None


class Safety(BaseModel):
    is_safe_location: bool | None = None
    needs_assistance: bool | None = None
    emergency_services_dispatched: bool | None = None
    injuries: bool | str | None = None
    police_report: bool | None = None
    police_report_details: str | None = None


class Documents(BaseModel):
    photos: bool | None = None
    receipts: bool | None = None
    police_report: bool | None = None


class ClaimState(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    session_id: str
    claim_type: str | None = None
    status: str | None = None
    disposition: str | None = None
    caller: Caller = Field(default_factory=Caller)
    policyholder: Policyholder = Field(default_factory=Policyholder)
    incident: Incident = Field(default_factory=Incident)
    driver: Driver = Field(default_factory=Driver)
    damage: Damage = Field(default_factory=Damage)
    third_parties: ThirdParties = Field(default_factory=ThirdParties)
    safety: Safety = Field(default_factory=Safety)
    documents: Documents = Field(default_factory=Documents)
    services: Services = Field(default_factory=Services)
    created_at: str = Field(default_factory=utc_now_iso)
    completed_at: str | None = None

    def merge_update(self, update: dict[str, Any]) -> list[str]:
        invalid_fields: list[str] = []
        for key, value in update.items():
            if value is None:
                continue
            if isinstance(value, dict) and "." not in key:
                for nested_key, nested_value in flatten_dict(value, key).items():
                    try:
                        self.set_path(nested_key, nested_value)
                    except ValueError:
                        invalid_fields.append(nested_key)
            else:
                try:
                    self.set_path(key, value)
                except ValueError:
                    invalid_fields.append(key)
        return invalid_fields

    def set_path(self, path: str, value: Any) -> None:
        target: Any = self
        parts = path.split(".")
        for part in parts[:-1]:
            if not hasattr(target, part):
                raise ValueError(f"Unknown claim field: {path}")
            target = getattr(target, part)

        leaf = parts[-1]
        if not hasattr(target, leaf):
            raise ValueError(f"Unknown claim field: {path}")
        if path == "damage.items" and isinstance(value, str):
            value = [item.strip() for item in value.split(",") if item.strip()]
        setattr(target, leaf, value)

    def get_path(self, path: str) -> Any:
        target: Any = self
        for part in path.split("."):
            if not hasattr(target, part):
                raise ValueError(f"Unknown claim field: {path}")
            target = getattr(target, part)
        return target

    def mark_completed(self) -> None:
        self.completed_at = utc_now_iso()

    def save(self, storage_dir: Path) -> Path:
        storage_dir.mkdir(parents=True, exist_ok=True)
        path = storage_dir / f"{self.session_id}_claim.json"
        path.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def summary(self) -> str:
        filled = {
            k: v for k, v in self.filled_fields().items()
            if k.split(".")[0] not in METADATA_FIELDS
        }
        if not filled:
            return "No fields collected yet"
        parts = [f"{k}={v!r}" for k, v in sorted(filled.items())]
        return "Collected so far: " + ", ".join(parts)

    def filled_fields(self) -> dict[str, Any]:
        flat = flatten_dict(self.model_dump(mode="json"))
        return {key: value for key, value in flat.items() if is_filled(value)}


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    items: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, path))
        else:
            items[path] = value
    return items


def is_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return True
