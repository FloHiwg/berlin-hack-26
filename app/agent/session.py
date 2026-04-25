from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from google import genai
from google.genai import types

from app.agent.prompts import build_system_prompt
from app.agent.schemas import tools
from app.agent.tools import ClaimToolHandlers, SessionFinished
from app.claims.claim_state import ClaimState
from app.claims.playbook_engine import PlaybookEngine


def new_session_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"claim_{stamp}_{uuid4().hex[:4]}"


class TranscriptLogger:
    def __init__(self, storage_dir: Path, session_id: str) -> None:
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.path = storage_dir / f"{session_id}.jsonl"

    def log(self, role: str, content: Any) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "role": role,
            "content": content,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


async def run_session(
    *,
    text_mode: bool,
    playbook_path: Path,
    storage_dir: Path,
    eval_transcript: Path | None = None,
) -> ClaimState:
    if not text_mode:
        raise NotImplementedError("Phase 1 supports --text-mode only.")

    playbook_engine = PlaybookEngine.from_yaml(playbook_path)
    claim_state = ClaimState(session_id=new_session_id())
    claim_state.save(storage_dir)
    logger = TranscriptLogger(storage_dir, claim_state.session_id)
    handlers = ClaimToolHandlers(claim_state, playbook_engine, storage_dir)

    print(f"Session ID: {claim_state.session_id}", flush=True)
    logger.log("session", {"session_id": claim_state.session_id})

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env or your shell.")

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-live-preview")
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        system_instruction=build_system_prompt(playbook_engine, claim_state),
        tools=tools,
    )

    async with client.aio.live.connect(model=model, config=config) as live_session:
        await send_user_turn(
            live_session,
            "Begin the claims intake now. Greet the customer and ask for the first required field.",
        )
        logger.log(
            "control",
            "Requested initial greeting and first claims intake question.",
        )
        receive_task = asyncio.create_task(
            receive_loop(live_session, handlers, logger)
        )
        send_task = asyncio.create_task(
            send_text_loop(live_session, logger, eval_transcript)
        )
        done, pending = await asyncio.wait(
            {receive_task, send_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if isinstance(exc, SessionFinished):
                pass
            elif exc is not None:
                raise exc

    return claim_state


async def send_text_loop(
    live_session: Any,
    logger: TranscriptLogger,
    eval_transcript: Path | None = None,
) -> None:
    if eval_transcript:
        lines = [
            line.strip()
            for line in eval_transcript.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for user_input in lines:
            print(f"\nYou: {user_input}", flush=True)
            await send_user_turn(live_session, user_input)
            logger.log("user", user_input)
        return

    while True:
        user_input = await asyncio.to_thread(input, "\nYou: ")
        if user_input.strip().lower() in {"exit", "quit"}:
            raise SessionFinished("user_exit")
        await send_user_turn(live_session, user_input)
        logger.log("user", user_input)


async def send_user_turn(live_session: Any, user_input: str) -> None:
    await live_session.send_client_content(
        turns=types.Content(role="user", parts=[types.Part(text=user_input)])
    )


async def receive_loop(
    live_session: Any,
    handlers: ClaimToolHandlers,
    logger: TranscriptLogger,
) -> None:
    model_buffer: list[str] = []
    async for response in live_session.receive():
        text = extract_text(response)
        if text:
            model_buffer.append(text)
            print(text, end="", flush=True)

        for call in extract_function_calls(response):
            if model_buffer:
                logger.log("model", "".join(model_buffer))
                model_buffer.clear()
            logger.log("tool_call", {"name": call["name"], "args": call["args"]})
            result = handlers.dispatch(call["name"], call["args"])
            logger.log("tool_response", {"name": call["name"], "result": result})
            await send_tool_response(live_session, call["name"], result, call.get("id"))
            if handlers.finished_reason:
                raise SessionFinished(handlers.finished_reason)


def extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    server_content = getattr(response, "server_content", None)
    model_turn = getattr(server_content, "model_turn", None)
    parts = getattr(model_turn, "parts", []) if model_turn else []
    chunks: list[str] = []
    for part in parts:
        part_text = getattr(part, "text", None)
        if part_text:
            chunks.append(part_text)
    return "".join(chunks)


def extract_function_calls(response: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    tool_call = getattr(response, "tool_call", None)
    function_calls = getattr(tool_call, "function_calls", []) if tool_call else []
    for function_call in function_calls:
        calls.append(
            {
                "id": getattr(function_call, "id", None),
                "name": getattr(function_call, "name", ""),
                "args": dict(getattr(function_call, "args", {}) or {}),
            }
        )
    return calls


async def send_tool_response(
    live_session: Any,
    name: str,
    result: dict[str, Any],
    call_id: str | None,
) -> None:
    response = types.FunctionResponse(
        name=name,
        response=result,
        id=call_id,
    )
    await live_session.send_tool_response(function_responses=[response])


def print_exception(exc: Exception) -> None:
    print(f"\nError: {exc}", file=sys.stderr, flush=True)
