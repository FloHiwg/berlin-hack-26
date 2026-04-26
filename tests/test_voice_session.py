import asyncio
import contextlib
from types import SimpleNamespace
import wave

import numpy as np
import pytest

from app.agent import session as session_mod
from app.agent.tools import SessionFinished
from app.audio import output as output_mod
from app.audio.ambient import AmbientLoopMixer


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
                    SimpleNamespace(
                        name="finalize_claim" if self.receive_calls == 2 else "end_call",
                        args={}
                        if self.receive_calls == 2
                        else {"reason": "Intake completed", "disposition": "intake_completed"},
                        id=f"call-{self.receive_calls - 1}",
                    )
                ]
            ),
        )

    async def send_tool_response(self, *args, **kwargs) -> None:
        return None


class _FakeHandlers:
    def __init__(self) -> None:
        self.finished_reason = None

    def dispatch(self, name, args):
        if name == "end_call":
            self.finished_reason = "ended"
            return {"status": "ended"}
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

    assert exc_info.value.reason == "ended"
    assert session.receive_calls == 3


def test_audio_recorder_preserves_timeline_gaps(tmp_path, monkeypatch) -> None:
    now = 1000.0
    monkeypatch.setattr(session_mod.time, "monotonic", lambda: now)
    recorder = session_mod.AudioRecorder(
        tmp_path,
        "session",
        suffix="agent",
        sample_rate=10,
        start_time=now,
    )

    now += 1.0
    recorder.add_chunk(np.array([100, 200], dtype=np.int16).tobytes())
    now += 2.0
    recorder.add_chunk(np.array([300, 400], dtype=np.int16).tobytes())

    rendered = recorder.to_array()

    assert rendered.tolist() == [0] * 10 + [100, 200] + [0] * 18 + [300, 400]


def test_audio_recorder_keeps_back_to_back_stream_chunks_contiguous(tmp_path, monkeypatch) -> None:
    now = 1000.0
    monkeypatch.setattr(session_mod.time, "monotonic", lambda: now)
    recorder = session_mod.AudioRecorder(
        tmp_path,
        "session",
        suffix="agent",
        sample_rate=10,
        start_time=now,
    )

    recorder.add_chunk(np.arange(10, dtype=np.int16).tobytes())
    now += 0.1
    recorder.add_chunk(np.arange(10, 20, dtype=np.int16).tobytes())

    assert recorder.to_array().tolist() == list(range(20))


def test_merge_audio_recordings_keeps_stream_offsets(tmp_path) -> None:
    caller_path = tmp_path / "caller.wav"
    agent_path = tmp_path / "agent.wav"
    output_path = tmp_path / "merged.wav"

    with wave.open(str(caller_path), "wb") as caller:
        caller.setnchannels(1)
        caller.setsampwidth(2)
        caller.setframerate(10)
        caller.writeframes(np.array([10] * 40, dtype=np.int16).tobytes())

    agent = np.array([0] * 20 + [100] * 10, dtype=np.int16)
    with wave.open(str(agent_path), "wb") as agent_wav:
        agent_wav.setnchannels(1)
        agent_wav.setsampwidth(2)
        agent_wav.setframerate(10)
        agent_wav.writeframes(agent.tobytes())

    session_mod.merge_audio_recordings(caller_path, agent_path, output_path, target_rate=10)

    with wave.open(str(output_path), "rb") as merged_wav:
        merged = np.frombuffer(merged_wav.readframes(merged_wav.getnframes()), dtype=np.int16)
    mixed_mono = merged.reshape(-1, 2)[:, 0]

    assert mixed_mono[:20].tolist() == [10] * 20
    assert mixed_mono[20:30].tolist() == [110] * 10


@pytest.mark.anyio
async def test_play_audio_keeps_ambient_alive_after_speech_chunk(monkeypatch) -> None:
    writes: list[np.ndarray] = []

    class _FakeStream:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

        def close(self) -> None:
            return None

        def write(self, audio: np.ndarray) -> None:
            writes.append(audio.copy())

    monkeypatch.setattr(output_mod.sd, "RawOutputStream", lambda **kwargs: _FakeStream())
    monkeypatch.setattr(
        output_mod,
        "_build_ambient_mixer",
        lambda: AmbientLoopMixer(
            sample_rate=24000,
            gain=1.0,
            audio_loop=np.array([5, 6], dtype=np.int16),
        ),
    )
    monkeypatch.setattr(output_mod, "_PLAYBACK_TAIL_SECONDS", 0.15)

    queue: asyncio.Queue = asyncio.Queue()
    await queue.put(np.array([10, 20], dtype=np.int16).tobytes())

    task = asyncio.create_task(output_mod.play_audio(queue))
    while len(writes) < 2:
        await asyncio.sleep(0)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert writes[0].tolist() == [15, 26]
    assert writes[1][:4].tolist() == [5, 6, 5, 6]
