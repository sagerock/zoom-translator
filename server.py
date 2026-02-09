"""Main WebSocket server — receives Recall.ai audio, runs the translation pipeline.

Serves the web UI on HTTP GET / and manages bots via a management WebSocket at /mgmt.
Recall.ai bots connect on the default path for audio streaming.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import signal
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

import websockets
from websockets.asyncio.server import serve, ServerConnection
from websockets.http11 import Request, Response

import config
from pipeline.asr import ASRStream
from pipeline.translator import translate
from pipeline.tts import synthesize
from recall_client import create_bot, stop_bot
from web_ui import HTML_PAGE, LISTEN_PAGE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


# ── Per-bot session state ──────────────────────────────────────────────

RECORDINGS_DIR = Path(__file__).parent / "recordings"


@dataclass
class BotSession:
    bot_id: str
    meeting_url: str
    source_lang: str
    target_lang: str
    status: str = "starting"  # starting | in_call | stopped
    asr_streams: dict[str, ASRStream] = field(default_factory=dict)
    recording_dir: Path | None = None
    recording_start: float = 0.0
    clip_count: int = 0
    audio_offset: float = 0.0  # cumulative audio seconds for SRT timing


# bot_id → BotSession
bot_sessions: dict[str, BotSession] = {}

# Connected management UI WebSocket clients
mgmt_clients: set[ServerConnection] = set()

# target_lang → set of WebSocket connections (listener browsers)
listener_clients: dict[str, set[ServerConnection]] = {}


# ── HTTP request handler (serves web UI) ──────────────────────────────

async def process_request(connection: ServerConnection, request: Request) -> Response | None:
    """Intercept HTTP requests to serve the web UI page.

    WebSocket upgrade requests (from Recall.ai bots or the management UI)
    are passed through by returning None.
    """
    # Let any WebSocket upgrade through immediately
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return None

    if request.path == "/" or request.path == "/index.html":
        response = connection.respond(200, HTML_PAGE)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    if request.path.startswith("/listen"):
        response = connection.respond(200, LISTEN_PAGE)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    if request.path == "/health":
        response = connection.respond(200, "ok")
        return response

    # Download recordings: /recordings/<bot_id>/<filename>
    if request.path.startswith("/recordings/"):
        parts = request.path.strip("/").split("/")
        if len(parts) == 3:
            bot_id, filename = parts[1], parts[2]
            rec_dir = RECORDINGS_DIR / bot_id
            # Serve concatenated audio on-the-fly
            if filename == "full_audio.mp3" and rec_dir.is_dir():
                data = _build_full_audio(rec_dir)
                if data:
                    response = connection.respond(200, data)
                    response.headers["Content-Type"] = "audio/mpeg"
                    response.headers["Content-Disposition"] = (
                        f'attachment; filename="{bot_id[:8]}_translation.mp3"'
                    )
                    return response
            # Serve SRT / transcript directly
            file_path = (rec_dir / filename).resolve()
            if file_path.parent == rec_dir.resolve() and file_path.is_file():
                ct_map = {".srt": "text/plain; charset=utf-8",
                          ".jsonl": "application/json; charset=utf-8"}
                ct = ct_map.get(file_path.suffix, "application/octet-stream")
                data = file_path.read_bytes()
                response = connection.respond(200, data)
                response.headers["Content-Type"] = ct
                response.headers["Content-Disposition"] = (
                    f'attachment; filename="{bot_id[:8]}_{filename}"'
                )
                return response
        return connection.respond(404, "Not Found")

    # Unknown non-WebSocket request
    return connection.respond(404, "Not Found")


# ── Management WebSocket broadcast ────────────────────────────────────

def _sessions_snapshot() -> list[dict]:
    return [
        {
            "bot_id": s.bot_id,
            "meeting_url": s.meeting_url,
            "source_lang": s.source_lang,
            "target_lang": s.target_lang,
            "status": s.status,
            "clip_count": s.clip_count,
        }
        for s in bot_sessions.values()
    ]


async def broadcast_status() -> None:
    """Send current bot status to all connected management clients."""
    msg = json.dumps({"type": "status", "bots": _sessions_snapshot()})
    stale = set()
    for ws in mgmt_clients:
        try:
            await ws.send(msg)
        except Exception:
            stale.add(ws)
    mgmt_clients.difference_update(stale)


# ── Management WebSocket handler (/mgmt) ──────────────────────────────

async def mgmt_handler(ws: ServerConnection) -> None:
    """Handle management WebSocket connections from the web UI."""
    mgmt_clients.add(ws)
    log.info("Management client connected")

    # Send current state immediately
    await ws.send(json.dumps({"type": "status", "bots": _sessions_snapshot()}))

    try:
        async for raw_msg in ws:
            try:
                msg = json.loads(raw_msg)
            except (json.JSONDecodeError, TypeError):
                await ws.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            action = msg.get("action")

            if action == "start":
                await _handle_start(ws, msg)
            elif action == "stop":
                await _handle_stop(ws, msg)
            else:
                await ws.send(json.dumps({"type": "error", "message": f"Unknown action: {action}"}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        mgmt_clients.discard(ws)
        log.info("Management client disconnected")


async def _handle_start(ws: ServerConnection, msg: dict) -> None:
    meeting_url = msg.get("meeting_url", "").strip()
    source_lang = msg.get("source_lang", "en")
    target_langs = msg.get("target_langs", [])

    if not meeting_url:
        await ws.send(json.dumps({"type": "error", "message": "Missing meeting_url"}))
        return
    if not target_langs:
        await ws.send(json.dumps({"type": "error", "message": "Select at least one target language"}))
        return

    for target_lang in target_langs:
        lang_upper = target_lang.upper()
        bot_name = f"Translator ({lang_upper})"
        try:
            bot_id = await create_bot(meeting_url, config.PUBLIC_WSS_URL, bot_name=bot_name)
            session = BotSession(
                bot_id=bot_id,
                meeting_url=meeting_url,
                source_lang=source_lang,
                target_lang=target_lang,
                status="in_call",
            )
            bot_sessions[bot_id] = session
            _init_recording(session)
            log.info("Started bot %s for %s → %s", bot_id, source_lang, target_lang)
        except Exception as e:
            log.exception("Failed to create bot for %s", target_lang)
            await ws.send(json.dumps({"type": "error", "message": f"Failed to create bot for {lang_upper}: {e}"}))

    await broadcast_status()


async def _handle_stop(ws: ServerConnection, msg: dict) -> None:
    bot_id = msg.get("bot_id", "").strip()
    session = bot_sessions.get(bot_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": f"Unknown bot: {bot_id}"}))
        return

    try:
        await stop_bot(bot_id)
    except Exception:
        log.exception("Error stopping bot %s", bot_id)

    # Clean up ASR streams
    for pid in list(session.asr_streams):
        stream = session.asr_streams.pop(pid, None)
        if stream:
            await stream.close()

    session.status = "stopped"
    await broadcast_status()

    # Remove from active sessions after broadcasting the stopped status
    bot_sessions.pop(bot_id, None)


# ── Listener WebSocket handler (/listen) ──────────────────────────────

async def listen_handler(ws: ServerConnection) -> None:
    """Handle listener browser WebSocket connections."""
    path = ws.request.path if ws.request else "/listen"
    qs = parse_qs(urlparse(path).query)
    lang = qs.get("lang", [""])[0].lower()

    if not lang:
        await ws.close(1008, "Missing ?lang= parameter")
        return

    if lang not in listener_clients:
        listener_clients[lang] = set()
    listener_clients[lang].add(ws)
    log.info("Listener connected for lang=%s (%d total)", lang, len(listener_clients[lang]))

    try:
        async for _ in ws:
            pass  # keep alive; listeners only receive, never send
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        listener_clients.get(lang, set()).discard(ws)
        remaining = len(listener_clients.get(lang, set()))
        log.info("Listener disconnected for lang=%s (%d remaining)", lang, remaining)


async def broadcast_audio(lang: str, mp3_b64: str, original: str = "", translated: str = "") -> None:
    """Send an MP3 audio clip to all listener browsers for a language."""
    clients = listener_clients.get(lang, set())
    if not clients:
        return
    msg = json.dumps({"type": "audio", "mp3": mp3_b64, "original": original, "translated": translated})
    stale = set()
    for ws in clients:
        try:
            await ws.send(msg)
        except Exception:
            stale.add(ws)
    clients.difference_update(stale)


# ── Recording ─────────────────────────────────────────────────────────

def _init_recording(session: BotSession) -> None:
    rec_dir = RECORDINGS_DIR / session.bot_id
    rec_dir.mkdir(parents=True, exist_ok=True)
    session.recording_dir = rec_dir
    session.recording_start = time.time()
    log.info("Recording to %s", rec_dir)


def _format_srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def save_recording(session: BotSession, mp3_b64: str, original: str, translated: str) -> None:
    if not session.recording_dir:
        return

    mp3_bytes = base64.b64decode(mp3_b64)
    session.clip_count += 1
    n = session.clip_count

    # Save individual clip
    clip_path = session.recording_dir / f"clip_{n:04d}.mp3"
    clip_path.write_bytes(mp3_bytes)

    # Estimate clip duration (~64 kbps = 8000 bytes/sec)
    duration = len(mp3_bytes) / 8000.0
    start = session.audio_offset
    session.audio_offset += duration

    # Append to SRT (timed to concatenated audio)
    srt_path = session.recording_dir / "subtitles.srt"
    with open(srt_path, "a", encoding="utf-8") as f:
        f.write(f"{n}\n")
        f.write(f"{_format_srt_time(start)} --> {_format_srt_time(session.audio_offset)}\n")
        f.write(f"{translated}\n\n")

    # Append to transcript (JSONL with wall-clock timestamp)
    transcript_path = session.recording_dir / "transcript.jsonl"
    elapsed = time.time() - session.recording_start
    entry = {
        "n": n,
        "elapsed": round(elapsed, 2),
        "audio_start": round(start, 2),
        "audio_end": round(session.audio_offset, 2),
        "original": original,
        "translated": translated,
    }
    with open(transcript_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _build_full_audio(rec_dir: Path) -> bytes:
    """Concatenate all clip MP3s into one file."""
    clips = sorted(rec_dir.glob("clip_*.mp3"))
    chunks = []
    for clip in clips:
        chunks.append(clip.read_bytes())
    return b"".join(chunks)


# ── Pipeline callback chain (per-session) ─────────────────────────────

def make_on_utterance(session: BotSession):
    """Create an utterance callback bound to a specific bot session."""
    async def on_utterance(participant_id: str, text: str) -> None:
        target_lang = session.target_lang
        translated = await translate(text, target_lang)
        if translated is None:
            return

        mp3_b64 = await synthesize(translated, target_lang)
        await broadcast_audio(target_lang, mp3_b64, original=text, translated=translated)
        save_recording(session, mp3_b64, text, translated)

    return on_utterance


# ── Recall.ai audio handler (default path) ────────────────────────────

async def recall_handler(ws: ServerConnection) -> None:
    """Handle Recall.ai bot WebSocket connections for audio streaming."""
    remote = ws.remote_address
    log.info("Recall.ai WebSocket connected from %s", remote)

    session: BotSession | None = None

    try:
        async for raw_msg in ws:
            try:
                msg: dict[str, Any] = json.loads(raw_msg)
            except (json.JSONDecodeError, TypeError):
                log.warning("Non-JSON message received, ignoring")
                continue

            event = msg.get("event")
            data = msg.get("data", {})

            # Extract bot_id from the message envelope and look up session
            if session is None:
                bot_data = data.get("bot") or {}
                incoming_bot_id = bot_data.get("id")
                if incoming_bot_id:
                    session = bot_sessions.get(incoming_bot_id)
                    if session:
                        log.info("Matched bot session: %s (%s → %s)",
                                 incoming_bot_id, session.source_lang, session.target_lang)
                    else:
                        log.warning("No session found for bot %s — using default config", incoming_bot_id)
                        # Create a fallback session for bots started via CLI
                        session = BotSession(
                            bot_id=incoming_bot_id,
                            meeting_url="",
                            source_lang="es",
                            target_lang=config.TARGET_LANGUAGE,
                            status="in_call",
                        )
                        bot_sessions[incoming_bot_id] = session
                        _init_recording(session)
                        await broadcast_status()

            if event == "audio_separate_raw.data":
                if session is None:
                    continue

                inner = data.get("data", {})
                participant = inner.get("participant", {})
                participant_id = str(participant.get("id", "unknown"))
                participant_name = participant.get("name", "")

                # Skip bot's own audio to avoid feedback loops
                if participant_name.startswith("Translator"):
                    continue

                audio_b64 = inner.get("buffer", "")
                if not audio_b64:
                    continue

                pcm_bytes = base64.b64decode(audio_b64)

                # Get or create ASR stream for this participant in this session
                if participant_id not in session.asr_streams:
                    on_utterance = make_on_utterance(session)
                    stream = ASRStream(participant_id, on_utterance, source_lang=session.source_lang)
                    await stream.start()
                    session.asr_streams[participant_id] = stream

                await session.asr_streams[participant_id].send_audio(pcm_bytes)

            elif event == "participant_events.leave":
                if session is None:
                    continue
                inner = data.get("data", {})
                participant_id = str(inner.get("participant", {}).get("id", ""))
                if participant_id:
                    log.info("Participant left: %s", participant_id)
                    stream = session.asr_streams.pop(participant_id, None)
                    if stream:
                        await stream.close()

            else:
                log.debug("Unhandled event: %s", event)

    except websockets.exceptions.ConnectionClosed:
        log.info("Recall.ai WebSocket closed from %s", remote)
    finally:
        # Tear down ASR streams for this session
        if session:
            for pid in list(session.asr_streams):
                stream = session.asr_streams.pop(pid, None)
                if stream:
                    await stream.close()


# ── Main handler with path routing ────────────────────────────────────

async def handler(ws: ServerConnection) -> None:
    """Route WebSocket connections based on request path."""
    path = ws.request.path if ws.request else "/"

    if path == "/mgmt":
        await mgmt_handler(ws)
    elif path.startswith("/listen"):
        await listen_handler(ws)
    else:
        await recall_handler(ws)


# ── Entry point ───────────────────────────────────────────────────────

async def main() -> None:
    stop = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    async with serve(
        handler,
        config.WEBSOCKET_HOST,
        config.WEBSOCKET_PORT,
        process_request=process_request,
    ):
        log.info(
            "Server listening on http://%s:%s",
            config.WEBSOCKET_HOST,
            config.WEBSOCKET_PORT,
        )
        await stop.wait()

    log.info("Server shut down.")


if __name__ == "__main__":
    asyncio.run(main())
