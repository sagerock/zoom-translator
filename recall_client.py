"""Recall.ai API client — create/stop bots and send audio back into Zoom."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import sys

import httpx

import config

log = logging.getLogger(__name__)


async def create_bot(meeting_url: str, websocket_url: str) -> str:
    """Deploy a Recall.ai bot to *meeting_url*.

    The bot streams per-participant audio to *websocket_url* over WebSocket.

    Returns:
        The bot ID.
    """
    # Minimal silent MP3 (1 frame of silence) to enable output_audio endpoint
    SILENT_MP3 = (
        "//uQxAAAAAANIAAAAAExBTUUzLjEwMFVVVVVVVVVVVVVVVVVV"
        "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    )

    payload = {
        "meeting_url": meeting_url,
        "bot_name": "Translator Bot",
        "recording_config": {
            "audio_separate_raw": {},
            "realtime_endpoints": [
                {
                    "type": "websocket",
                    "url": websocket_url,
                    "events": ["audio_separate_raw.data"],
                }
            ],
        },
        "automatic_audio_output": {
            "in_call_recording": {
                "data": {
                    "kind": "mp3",
                    "b64_data": SILENT_MP3,
                },
            },
        },
    }

    headers = {
        "Authorization": f"Token {config.RECALL_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{config.RECALL_API_BASE}/bot",
            json=payload,
            headers=headers,
        )

    resp.raise_for_status()
    data = resp.json()
    bot_id = data["id"]
    log.info("Bot created: %s", bot_id)
    return bot_id


async def stop_bot(bot_id: str) -> None:
    """Remove the bot from the meeting."""
    headers = {"Authorization": f"Token {config.RECALL_API_KEY}"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{config.RECALL_API_BASE}/bot/{bot_id}/leave_call",
            headers=headers,
        )

    resp.raise_for_status()
    log.info("Bot stopped: %s", bot_id)


async def send_audio(bot_id: str, mp3_base64: str) -> None:
    """Play an MP3 clip into the Zoom meeting via Recall.ai Output Audio API."""
    headers = {
        "Authorization": f"Token {config.RECALL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "kind": "mp3",
        "b64_data": mp3_base64,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{config.RECALL_API_BASE}/bot/{bot_id}/output_audio",
            json=payload,
            headers=headers,
        )

    if resp.status_code not in (200, 201):
        log.error("send_audio failed %s: %s", resp.status_code, resp.text)
    else:
        log.info("Audio sent to bot %s", bot_id)


# ── CLI helper ──────────────────────────────────────────────────────────
async def _cli() -> None:
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python recall_client.py create <meeting_url> <websocket_url>")
        print("  python recall_client.py stop   <bot_id>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create":
        meeting_url = sys.argv[2]
        ws_url = sys.argv[3] if len(sys.argv) > 3 else f"ws://localhost:{config.WEBSOCKET_PORT}"
        bot_id = await create_bot(meeting_url, ws_url)
        print(f"Bot ID: {bot_id}")

    elif cmd == "stop":
        bot_id = sys.argv[2]
        await stop_bot(bot_id)
        print("Bot stopped.")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(_cli())
