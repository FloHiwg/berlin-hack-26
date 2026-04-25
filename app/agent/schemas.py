from __future__ import annotations

from google.genai import types


def _schema_type(name: str):
    return getattr(types.Type, name, name)


update_claim_state_tool = types.FunctionDeclaration(
    name="update_claim_state",
    description="Call after every user answer to record extracted claim fields.",
    parameters=types.Schema(
        type=_schema_type("OBJECT"),
        properties={
            "claim_update": types.Schema(
                type=_schema_type("OBJECT"),
                description="Partial claim dict with dot-notation keys and extracted values.",
            )
        },
        required=["claim_update"],
    ),
)

escalate_tool = types.FunctionDeclaration(
    name="escalate",
    description="Call when urgent risk, injury, or human handoff is required.",
    parameters=types.Schema(
        type=_schema_type("OBJECT"),
        properties={
            "reason": types.Schema(type=_schema_type("STRING")),
            "risk_flags": types.Schema(
                type=_schema_type("ARRAY"), items=types.Schema(type=_schema_type("STRING"))
            ),
        },
        required=["reason", "risk_flags"],
    ),
)

finalize_claim_tool = types.FunctionDeclaration(
    name="finalize_claim",
    description="Call when all required fields for the current playbook stage are collected.",
    parameters=types.Schema(type=_schema_type("OBJECT"), properties={}),
)

tools = [
    types.Tool(
        function_declarations=[
            update_claim_state_tool,
            escalate_tool,
            finalize_claim_tool,
        ]
    )
]
