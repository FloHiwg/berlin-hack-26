from __future__ import annotations

import asyncio

import numpy as np
import sounddevice as sd

from app.audio.ambient import AmbientLoopMixer
from app.config import ambient_office_config

_SAMPLE_RATE = 24000
_PLAYBACK_TAIL_SECONDS = 0.25

# Sentinel pushed to the queue by the receive loop on barge-in.
FLUSH = object()


async def play_audio(
    queue: asyncio.Queue,
    speaking_event: asyncio.Event | None = None,
) -> None:
    """Read PCM chunks from *queue* and play them. FLUSH drains pending audio."""
    ambient_mixer: AmbientLoopMixer | None = None
    ambient_cfg = ambient_office_config()
    if ambient_cfg.enabled and ambient_cfg.gain > 0:
        try:
            ambient_mixer = AmbientLoopMixer.from_wav(
                sample_rate=_SAMPLE_RATE,
                gain=ambient_cfg.gain,
                wav_path=ambient_cfg.file_path,
            )
            print(
                f"[audio] office ambience enabled ({ambient_cfg.file_path}, gain={ambient_cfg.gain:.2f})",
                flush=True,
            )
        except Exception as exc:
            print(f"[audio] office ambience disabled: {exc}", flush=True)

    stream = sd.RawOutputStream(samplerate=_SAMPLE_RATE, channels=1, dtype="int16")
    stream.start()
    try:
        while True:
            chunk = await queue.get()
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
            pcm = np.frombuffer(chunk, dtype="int16")
            if ambient_mixer is not None:
                pcm = ambient_mixer.mix(pcm)
            await asyncio.to_thread(stream.write, pcm)
            if speaking_event and queue.empty():
                await asyncio.sleep(_PLAYBACK_TAIL_SECONDS)
                if queue.empty():
                    speaking_event.clear()
    finally:
        if speaking_event:
            speaking_event.clear()
        stream.stop()
        stream.close()
