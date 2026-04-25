import asyncio
from types import SimpleNamespace

import pytest

from app.agent import session as session_mod
from app.agent.tools import SessionFinished


class _FakeVoiceSession:
    def __init__(self) -> None:
        self.receive_calls = 0

    async def receive(self):
        self.receive_calls += 1
        if self.receive_calls == 1:
            yield SimpleNamespace(
                server_content=SimpleNamespace(
                    interrupted=False,
                    model_turn=SimpleNamespace(parts=[]),
                ),
                tool_call=None,
            )
            return

        yield SimpleNamespace(
            server_content=None,
            tool_call=SimpleNamespace(
                function_calls=[
                    SimpleNamespace(name="finalize_claim", args={}, id="call-1")
                ]
            ),
        )

    async def send_tool_response(self, *args, **kwargs) -> None:
        return None


class _FakeHandlers:
    def __init__(self) -> None:
        self.finished_reason = None

    def dispatch(self, name, args):
        self.finished_reason = "finalized"
        return {"status": "finalized"}


class _FakeLogger:
    def log(self, role, content) -> None:
        return None


@pytest.mark.anyio
async def test_voice_receive_loop_keeps_listening_after_one_model_turn() -> None:
    session = _FakeVoiceSession()

    with pytest.raises(SessionFinished) as exc_info:
        await session_mod._receive_voice_loop(
            session=session,
            handlers=_FakeHandlers(),
            logger=_FakeLogger(),
            audio_queue=asyncio.Queue(),
            flush_sentinel=object(),
        )

    assert exc_info.value.reason == "finalized"
    assert session.receive_calls == 2
