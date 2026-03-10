"""Main WebSocket server — receives Recall.ai audio, runs the translation pipeline.

Serves the web UI on HTTP GET / and manages bots via a management WebSocket at /mgmt.
Recall.ai bots connect on the default path for audio streaming.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse, parse_qs

import httpx

import websockets
from websockets.asyncio.server import serve, ServerConnection
from websockets.http11 import Request, Response

import config
import supabase_client
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


@dataclass
class BotSession:
    bot_id: str
    meeting_url: str
    source_lang: str
    target_lang: str
    user_id: str = ""
    status: str = "starting"  # starting | in_call | stopped
    asr_streams: dict[str, ASRStream] = field(default_factory=dict)
    recording_start: float = 0.0
    clip_count: int = 0
    audio_offset: float = 0.0  # cumulative audio seconds for SRT timing
    srt_buffer: str = ""
    transcript_buffer: str = ""


# bot_id → BotSession
bot_sessions: dict[str, BotSession] = {}

# Connected management UI WebSocket clients: ws → {user_id, is_admin}
mgmt_clients: dict[ServerConnection, dict] = {}

# target_lang → set of WebSocket connections (listener browsers)
listener_clients: dict[str, set[ServerConnection]] = {}


# ── Auth helpers ───────────────────────────────────────────────────────

ADMIN_EMAILS = {"sage@sagerock.com"}


def _is_admin(user: dict) -> bool:
    return user.get("email", "").lower() in ADMIN_EMAILS


async def _extract_user_from_header(request: Request) -> dict | None:
    """Extract and verify JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return await supabase_client.verify_jwt(auth[7:])
    return None


# ── Timeline-synced MP3 builder ────────────────────────────────────────

async def _build_synced_mp3(owner_id: str, bot_id: str) -> bytes:
    """Download all clips, read transcript timing, and build a single
    timeline-synced MP3 using ffmpeg with silence gaps."""

    # 1. Get signed URL for transcript.jsonl and all clips
    transcript_url = await supabase_client.get_signed_url(
        f"{owner_id}/{bot_id}/transcript.jsonl"
    )
    if not transcript_url:
        raise ValueError("transcript.jsonl not found")

    # 2. Download transcript to get elapsed timestamps
    async with httpx.AsyncClient() as client:
        resp = await client.get(transcript_url)
        resp.raise_for_status()
    entries = []
    for line in resp.text.strip().split("\n"):
        if line.strip():
            entries.append(json.loads(line))
    entries.sort(key=lambda e: e["n"])

    if not entries:
        raise ValueError("No entries in transcript")

    clip_count = len(entries)
    log.info("Building synced MP3 for %s: %d clips", bot_id[:8], clip_count)

    # 3. Get signed URLs for all clips (batched)
    BATCH = 20
    clip_urls = {}
    for batch_start in range(1, clip_count + 1, BATCH):
        batch_end = min(batch_start + BATCH, clip_count + 1)
        tasks = {
            i: supabase_client.get_signed_url(f"{owner_id}/{bot_id}/clip_{i:04d}.mp3")
            for i in range(batch_start, batch_end)
        }
        results = await asyncio.gather(*tasks.values())
        for i, url in zip(tasks.keys(), results):
            if url:
                clip_urls[i] = url

    # 4. Download all clips (batched)
    DL_BATCH = 10
    clip_data: dict[int, bytes] = {}
    clip_nums = sorted(clip_urls.keys())

    async with httpx.AsyncClient() as client:
        for batch_start in range(0, len(clip_nums), DL_BATCH):
            batch = clip_nums[batch_start:batch_start + DL_BATCH]

            async def _download(n: int) -> tuple[int, bytes]:
                r = await client.get(clip_urls[n])
                r.raise_for_status()
                return n, r.content

            results = await asyncio.gather(*[_download(n) for n in batch])
            for n, data in results:
                clip_data[n] = data

    # 5. Build the synced MP3 with ffmpeg in a temp directory
    mp3_bytes = await asyncio.to_thread(
        _ffmpeg_build_synced, entries, clip_data
    )
    log.info("Synced MP3 built for %s: %.1f MB", bot_id[:8], len(mp3_bytes) / 1_000_000)
    return mp3_bytes


def _ffmpeg_build_synced(entries: list[dict], clip_data: dict[int, bytes]) -> bytes:
    """Use ffmpeg to place clips at their elapsed timestamps with silence gaps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write each clip to a temp file
        for n, data in clip_data.items():
            with open(os.path.join(tmpdir, f"clip_{n:04d}.mp3"), "wb") as f:
                f.write(data)

        # Build ffmpeg concat file with silence gaps
        # We'll create silence segments between clips
        total_elapsed = entries[-1]["elapsed"]
        # Estimate last clip duration from audio_end - audio_start
        last_entry = entries[-1]
        last_clip_dur = last_entry.get("audio_end", 0) - last_entry.get("audio_start", 0)
        total_duration = total_elapsed + max(last_clip_dur, 1.0)

        # Build a filter that delays each clip to its elapsed position and mixes them
        # For large numbers of clips, we use a concat approach with silence instead
        concat_list = os.path.join(tmpdir, "concat.txt")
        prev_end = 0.0

        with open(concat_list, "w") as f:
            for entry in entries:
                n = entry["n"]
                if n not in clip_data:
                    continue
                elapsed = entry["elapsed"]
                clip_dur = entry.get("audio_end", 0) - entry.get("audio_start", 0)

                # Insert silence gap if needed
                gap = elapsed - prev_end
                if gap > 0.05:  # skip tiny gaps
                    silence_path = os.path.join(tmpdir, f"silence_{n:04d}.mp3")
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi",
                        "-i", f"anullsrc=r=44100:cl=mono",
                        "-t", f"{gap:.3f}",
                        "-c:a", "libmp3lame", "-b:a", "64k",
                        silence_path,
                    ], capture_output=True, check=True)
                    f.write(f"file '{silence_path}'\n")

                clip_path = os.path.join(tmpdir, f"clip_{n:04d}.mp3")
                f.write(f"file '{clip_path}'\n")
                prev_end = elapsed + clip_dur

        # Concatenate everything into final MP3
        output_path = os.path.join(tmpdir, "output.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c:a", "libmp3lame", "-b:a", "64k",
            output_path,
        ], capture_output=True, check=True)

        with open(output_path, "rb") as f:
            return f.read()


async def _build_synced_srt(owner_id: str, bot_id: str) -> str:
    """Generate SRT with elapsed-based timestamps that sync with the meeting video."""
    transcript_url = await supabase_client.get_signed_url(
        f"{owner_id}/{bot_id}/transcript.jsonl"
    )
    if not transcript_url:
        raise ValueError("transcript.jsonl not found")

    async with httpx.AsyncClient() as client:
        resp = await client.get(transcript_url)
        resp.raise_for_status()

    entries = []
    for line in resp.text.strip().split("\n"):
        if line.strip():
            entries.append(json.loads(line))
    entries.sort(key=lambda e: e["n"])

    srt = ""
    for entry in entries:
        n = entry["n"]
        start = entry["elapsed"]
        clip_dur = entry.get("audio_end", 0) - entry.get("audio_start", 0)
        end = start + max(clip_dur, 0.5)
        srt += f"{n}\n"
        srt += f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n"
        srt += f"{entry.get('translated', '')}\n\n"

    return srt


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
        page = HTML_PAGE.replace("__SUPABASE_URL__", config.SUPABASE_URL)
        page = page.replace("__SUPABASE_ANON_KEY__", config.SUPABASE_ANON_KEY)
        response = connection.respond(200, page)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    if request.path.startswith("/listen"):
        response = connection.respond(200, LISTEN_PAGE)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    if request.path == "/health":
        response = connection.respond(200, "ok")
        return response

    # API: list user's recordings from Supabase
    if request.path == "/api/recordings":
        user = await _extract_user_from_header(request)
        if not user:
            return connection.respond(401, "Unauthorized")
        user_id = user["sub"]
        sessions = await supabase_client.get_user_sessions(user_id)
        recordings = []
        for s in sessions:
            if s.get("clip_count", 0) > 0:
                recordings.append({
                    "bot_id": s["bot_id"],
                    "clips": s["clip_count"],
                    "duration": s.get("duration"),
                    "status": s.get("status"),
                })
        body = json.dumps(recordings)
        response = connection.respond(200, body)
        response.headers["Content-Type"] = "application/json"
        return response

    # API: admin — list all sessions across all users
    if request.path == "/api/admin/sessions":
        user = await _extract_user_from_header(request)
        if not user or not _is_admin(user):
            return connection.respond(403, "Forbidden")
        sessions = await supabase_client.get_all_sessions()
        recordings = []
        for s in sessions:
            if s.get("clip_count", 0) > 0:
                recordings.append({
                    "bot_id": s["bot_id"],
                    "user_id": s.get("user_id", ""),
                    "clips": s["clip_count"],
                    "duration": s.get("duration"),
                    "status": s.get("status"),
                    "source_lang": s.get("source_lang", ""),
                    "target_lang": s.get("target_lang", ""),
                    "created_at": s.get("created_at", ""),
                })
        body = json.dumps(recordings)
        response = connection.respond(200, body)
        response.headers["Content-Type"] = "application/json"
        return response

    # API: generate timeline-synced MP3 from all clips
    if request.path.startswith("/api/recordings/") and request.path.endswith("/audio"):
        user = await _extract_user_from_header(request)
        if not user:
            return connection.respond(401, "Unauthorized")
        user_id = user["sub"]
        admin = _is_admin(user)
        parts = request.path.strip("/").split("/")
        if len(parts) == 4:
            bot_id = parts[2]
            session = await supabase_client.get_session_by_bot_id(bot_id)
            if not session or (not admin and session.get("user_id") != user_id):
                return connection.respond(403, "Forbidden")
            owner_id = session.get("user_id", user_id)
            try:
                mp3_bytes = await _build_synced_mp3(owner_id, bot_id)
            except Exception:
                log.exception("Failed to build synced MP3 for %s", bot_id)
                return connection.respond(500, "Failed to generate audio")
            response = connection.respond(200, mp3_bytes)
            response.headers["Content-Type"] = "audio/mpeg"
            response.headers["Content-Disposition"] = f'attachment; filename="{bot_id[:8]}_translation.mp3"'
            return response
        return connection.respond(404, "Not Found")

    # Download recordings: /recordings/<bot_id>/<filename>
    if request.path.startswith("/recordings/"):
        user = await _extract_user_from_header(request)
        if not user:
            return connection.respond(401, "Unauthorized")
        user_id = user["sub"]
        admin = _is_admin(user)
        parts = request.path.strip("/").split("/")
        if len(parts) == 3:
            bot_id, filename = parts[1], parts[2]
            session = await supabase_client.get_session_by_bot_id(bot_id)
            if not session or (not admin and session.get("user_id") != user_id):
                return connection.respond(403, "Forbidden")
            owner_id = session.get("user_id", user_id)

            # Generate synced SRT from transcript.jsonl elapsed timestamps
            if filename == "subtitles.srt":
                try:
                    srt_text = await _build_synced_srt(owner_id, bot_id)
                except Exception:
                    log.exception("Failed to build synced SRT for %s", bot_id)
                    return connection.respond(500, "Failed to generate subtitles")
                response = connection.respond(200, srt_text)
                response.headers["Content-Type"] = "text/plain; charset=utf-8"
                response.headers["Content-Disposition"] = f'attachment; filename="{bot_id[:8]}_subtitles.srt"'
                return response

            # Other files (transcript.jsonl, etc.) → redirect to signed URL
            path = f"{owner_id}/{bot_id}/{filename}"
            signed_url = await supabase_client.get_signed_url(path)
            if signed_url:
                response = connection.respond(302, "")
                response.headers["Location"] = signed_url
                return response
        return connection.respond(404, "Not Found")

    # Unknown non-WebSocket request
    return connection.respond(404, "Not Found")


# ── Management WebSocket broadcast ────────────────────────────────────

def _sessions_snapshot(user_id: str, admin: bool = False) -> list[dict]:
    """Return bot sessions belonging to a specific user (or all if admin)."""
    result = []
    for s in bot_sessions.values():
        if not admin and s.user_id != user_id:
            continue
        entry = {
            "bot_id": s.bot_id,
            "meeting_url": s.meeting_url,
            "source_lang": s.source_lang,
            "target_lang": s.target_lang,
            "status": s.status,
            "clip_count": s.clip_count,
        }
        if admin:
            entry["user_id"] = s.user_id
        result.append(entry)
    return result


async def broadcast_status() -> None:
    """Send current bot status to all connected management clients, filtered by user."""
    stale = set()
    for ws, info in mgmt_clients.items():
        try:
            snapshot = _sessions_snapshot(info["user_id"], admin=info["is_admin"])
            msg = json.dumps({"type": "status", "bots": snapshot})
            await ws.send(msg)
        except Exception:
            stale.add(ws)
    for ws in stale:
        mgmt_clients.pop(ws, None)


# ── Management WebSocket handler (/mgmt) ──────────────────────────────

async def mgmt_handler(ws: ServerConnection, user: dict) -> None:
    """Handle management WebSocket connections from the web UI."""
    user_id = user["sub"]
    admin = _is_admin(user)
    mgmt_clients[ws] = {"user_id": user_id, "is_admin": admin}
    log.info("Management client connected (user=%s, admin=%s)", user_id[:8], admin)

    # Send current state immediately (include admin flag so UI can adapt)
    snapshot = _sessions_snapshot(user_id, admin=admin)
    await ws.send(json.dumps({"type": "status", "bots": snapshot, "is_admin": admin}))

    try:
        async for raw_msg in ws:
            try:
                msg = json.loads(raw_msg)
            except (json.JSONDecodeError, TypeError):
                await ws.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            action = msg.get("action")

            if action == "start":
                await _handle_start(ws, msg, user_id)
            elif action == "stop":
                await _handle_stop(ws, msg, user_id, admin)
            else:
                await ws.send(json.dumps({"type": "error", "message": f"Unknown action: {action}"}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        mgmt_clients.pop(ws, None)
        log.info("Management client disconnected (user=%s)", user_id[:8])


async def _handle_start(ws: ServerConnection, msg: dict, user_id: str) -> None:
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
                user_id=user_id,
                status="in_call",
            )
            bot_sessions[bot_id] = session
            _init_recording(session)

            # Persist to Supabase DB
            asyncio.create_task(supabase_client.create_session(
                user_id=user_id,
                bot_id=bot_id,
                meeting_url=meeting_url,
                source_lang=source_lang,
                target_lang=target_lang,
            ))

            log.info("Started bot %s for %s → %s (user=%s)", bot_id, source_lang, target_lang, user_id[:8])
        except Exception as e:
            log.exception("Failed to create bot for %s", target_lang)
            await ws.send(json.dumps({"type": "error", "message": f"Failed to create bot for {lang_upper}: {e}"}))

    await broadcast_status()


async def _handle_stop(ws: ServerConnection, msg: dict, user_id: str, admin: bool = False) -> None:
    bot_id = msg.get("bot_id", "").strip()
    session = bot_sessions.get(bot_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": f"Unknown bot: {bot_id}"}))
        return

    # Verify ownership (admins can stop any bot)
    if not admin and session.user_id != user_id:
        await ws.send(json.dumps({"type": "error", "message": "Not authorized to stop this bot"}))
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

    # Upload final SRT and transcript to Supabase Storage
    duration = session.audio_offset
    if session.srt_buffer:
        asyncio.create_task(supabase_client.upload_text_file(
            session.user_id, bot_id, "subtitles.srt", session.srt_buffer
        ))
    if session.transcript_buffer:
        asyncio.create_task(supabase_client.upload_text_file(
            session.user_id, bot_id, "transcript.jsonl", session.transcript_buffer
        ))

    # Update DB status
    asyncio.create_task(supabase_client.update_session_status(
        bot_id, "stopped", clip_count=session.clip_count, duration=round(duration, 1)
    ))

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
    session.recording_start = time.time()
    session.srt_buffer = ""
    session.transcript_buffer = ""
    log.info("Recording initialized for bot %s (cloud storage)", session.bot_id)


def _format_srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def save_recording(session: BotSession, mp3_b64: str, original: str, translated: str) -> None:
    mp3_bytes = base64.b64decode(mp3_b64)
    session.clip_count += 1
    n = session.clip_count

    # Upload clip to Supabase Storage (fire-and-forget)
    asyncio.create_task(supabase_client.upload_clip(
        session.user_id, session.bot_id, n, mp3_bytes
    ))

    # Estimate clip duration (~64 kbps = 8000 bytes/sec)
    duration = len(mp3_bytes) / 8000.0
    start = session.audio_offset
    session.audio_offset += duration

    # Append to in-memory SRT buffer
    session.srt_buffer += f"{n}\n"
    session.srt_buffer += f"{_format_srt_time(start)} --> {_format_srt_time(session.audio_offset)}\n"
    session.srt_buffer += f"{translated}\n\n"

    # Append to in-memory transcript buffer (JSONL)
    elapsed = time.time() - session.recording_start
    entry = {
        "n": n,
        "elapsed": round(elapsed, 2),
        "audio_start": round(start, 2),
        "audio_end": round(session.audio_offset, 2),
        "original": original,
        "translated": translated,
    }
    session.transcript_buffer += json.dumps(entry, ensure_ascii=False) + "\n"

    # Update DB clip count periodically (fire-and-forget)
    asyncio.create_task(supabase_client.update_session_status(
        session.bot_id, "in_call", clip_count=n
    ))


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
    parsed = urlparse(path)

    if parsed.path == "/mgmt":
        # Validate JWT from query string
        token = parse_qs(parsed.query).get("token", [""])[0]
        user = await supabase_client.verify_jwt(token)
        if not user:
            await ws.close(1008, "Invalid auth token")
            return
        await mgmt_handler(ws, user)
    elif parsed.path.startswith("/listen"):
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
