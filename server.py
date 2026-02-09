"""Main WebSocket server — receives Recall.ai audio, runs the translation pipeline."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import signal
import sys
from typing import Any

import websockets
from websockets.asyncio.server import serve, ServerConnection

import config
from pipeline.asr import ASRStream
from pipeline.translator import translate
from pipeline.tts import synthesize
from recall_client import send_audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ── Global state ────────────────────────────────────────────────────────

# bot_id is set once the first WebSocket message arrives (or via CLI arg)
bot_id: str | None = None

# participant_id → ASRStream
asr_streams: dict[str, ASRStream] = {}

# Name of the bot itself — used to filter out its own audio
BOT_PARTICIPANT_NAME = "Translator Bot"


# ── Pipeline callback chain ────────────────────────────────────────────

async def on_utterance(participant_id: str, text: str) -> None:
    """Called when Deepgram finalises an utterance for a participant."""
    target_lang = config.PARTICIPANT_LANGUAGES.get(participant_id, config.TARGET_LANGUAGE)

    translated = await translate(text, target_lang)
    if translated is None:
        return  # same language or error

    mp3_b64 = await synthesize(translated, target_lang)

    if bot_id:
        await send_audio(bot_id, mp3_b64)
    else:
        log.warning("No bot_id set — cannot send audio back to Zoom")


# ── Audio routing ───────────────────────────────────────────────────────

async def get_or_create_asr(participant_id: str) -> ASRStream:
    """Return the existing ASR stream for a participant, or create one."""
    if participant_id not in asr_streams:
        stream = ASRStream(participant_id, on_utterance)
        await stream.start()
        asr_streams[participant_id] = stream
    return asr_streams[participant_id]


async def remove_asr(participant_id: str) -> None:
    stream = asr_streams.pop(participant_id, None)
    if stream:
        await stream.close()


# ── WebSocket handler ───────────────────────────────────────────────────

async def handler(ws: ServerConnection) -> None:
    global bot_id

    remote = ws.remote_address
    log.info("WebSocket connected from %s", remote)

    try:
        async for raw_msg in ws:
            try:
                msg: dict[str, Any] = json.loads(raw_msg)
            except (json.JSONDecodeError, TypeError):
                log.warning("Non-JSON message received, ignoring")
                continue

            event = msg.get("event")
            data = msg.get("data", {})

            # Recall.ai sends a bot_id in the initial handshake
            if "bot_id" in msg and bot_id is None:
                bot_id = msg["bot_id"]
                log.info("Bot ID set: %s", bot_id)

            if "bot_id" in data and bot_id is None:
                bot_id = data["bot_id"]
                log.info("Bot ID set: %s", bot_id)

            if event == "audio.data" or event == "audio_raw.data":
                participant_id = str(data.get("participant_id", "unknown"))
                participant_name = data.get("participant_name", "")

                # Skip the bot's own audio to avoid feedback loops
                if participant_name == BOT_PARTICIPANT_NAME:
                    continue

                audio_b64 = data.get("data", "")
                if not audio_b64:
                    continue

                pcm_bytes = base64.b64decode(audio_b64)
                stream = await get_or_create_asr(participant_id)
                await stream.send_audio(pcm_bytes)

            elif event == "participant.leave":
                participant_id = str(data.get("participant_id", ""))
                if participant_id:
                    log.info("Participant left: %s", participant_id)
                    await remove_asr(participant_id)

            elif event == "bot.status_change":
                status = data.get("status", {})
                log.info("Bot status: %s", status)

            else:
                log.debug("Unhandled event: %s", event)

    except websockets.exceptions.ConnectionClosed:
        log.info("WebSocket closed from %s", remote)
    finally:
        # Tear down all ASR streams when the connection drops
        for pid in list(asr_streams):
            await remove_asr(pid)


# ── Entry point ─────────────────────────────────────────────────────────

async def main() -> None:
    global bot_id

    # Allow passing bot_id as a CLI argument for convenience
    if len(sys.argv) > 1:
        bot_id = sys.argv[1]
        log.info("Bot ID from CLI: %s", bot_id)

    stop = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    async with serve(handler, config.WEBSOCKET_HOST, config.WEBSOCKET_PORT):
        log.info(
            "WebSocket server listening on ws://%s:%s",
            config.WEBSOCKET_HOST,
            config.WEBSOCKET_PORT,
        )
        await stop.wait()

    log.info("Server shut down.")


if __name__ == "__main__":
    asyncio.run(main())
