from __future__ import annotations

import asyncio
import time

import numpy as np
import sounddevice as sd

from app.audio.ambient import AmbientLoopMixer
from app.config import ambient_office_config

_SAMPLE_RATE = 24000
_PLAYBACK_TAIL_SECONDS = 0.25
_AMBIENT_FRAME_SECONDS = 0.10
_AMBIENT_FRAME_SAMPLES = int(_SAMPLE_RATE * _AMBIENT_FRAME_SECONDS)

# Sentinel pushed to the queue by the receive loop on barge-in.
FLUSH = object()


def _build_ambient_mixer() -> AmbientLoopMixer | None:
    config = ambient_office_config()
    if not config.enabled or config.gain <= 0.0:
        return None
    try:
        return AmbientLoopMixer.from_wav(
            sample_rate=_SAMPLE_RATE,
            gain=config.gain,
            wav_path=config.file_path,
        )
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        print(f"[audio] ambient disabled: {exc}", flush=True)
        return None


async def _write_ambient_frame(stream: sd.RawOutputStream, ambient_mixer: AmbientLoopMixer) -> None:
    ambient_only = ambient_mixer.mix(np.zeros(_AMBIENT_FRAME_SAMPLES, dtype=np.int16))
    await asyncio.to_thread(stream.write, ambient_only)


async def _keep_ambient_alive_during_tail(
    queue: asyncio.Queue,
    stream: sd.RawOutputStream,
    ambient_mixer: AmbientLoopMixer | None,
) -> object | None:
    deadline = time.monotonic() + _PLAYBACK_TAIL_SECONDS
    while queue.empty():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        if ambient_mixer is None:
            try:
                return await asyncio.wait_for(queue.get(), timeout=remaining)
            except asyncio.TimeoutError:
                return None
        await _write_ambient_frame(stream, ambient_mixer)
    return await queue.get()


async def play_audio(
    queue: asyncio.Queue,
    speaking_event: asyncio.Event | None = None,
) -> None:
    """Read PCM chunks from *queue* and play them. FLUSH drains pending audio."""
    ambient_mixer = _build_ambient_mixer()
    stream = sd.RawOutputStream(samplerate=_SAMPLE_RATE, channels=1, dtype="int16")
    stream.start()
    pending_chunk: object | None = None
    try:
        while True:
            if pending_chunk is None:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=_AMBIENT_FRAME_SECONDS)
                except asyncio.TimeoutError:
                    if ambient_mixer is None:
                        continue
                    await _write_ambient_frame(stream, ambient_mixer)
                    continue
            else:
                chunk = pending_chunk
                pending_chunk = None
            if chunk is FLUSH:
                # Drain any audio chunks that arrived before the interrupt signal.
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                stream.stop()
                stream.start()
                if speaking_event:
                    speaking_event.clear()
                continue
            if speaking_event:
                speaking_event.set()
            speech = np.frombuffer(chunk, dtype="int16")
            if ambient_mixer is not None:
                speech = ambient_mixer.mix(speech)
            await asyncio.to_thread(stream.write, speech)
            if speaking_event and queue.empty():
                pending_chunk = await _keep_ambient_alive_during_tail(queue, stream, ambient_mixer)
                if pending_chunk is None:
                    speaking_event.clear()
    finally:
        if speaking_event:
            speaking_event.clear()
        stream.stop()
        stream.close()
