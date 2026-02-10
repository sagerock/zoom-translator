"""Supabase wrapper — auth, database, and storage helpers.

Uses the service-role key server-side (bypasses RLS for writes).
All synchronous Supabase SDK calls are wrapped in asyncio.to_thread()
to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from supabase import create_client, Client

import config

log = logging.getLogger(__name__)

# Service-role client — full access, used server-side only
_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)


# ── Auth ──────────────────────────────────────────────────────────────

async def verify_jwt(token: str) -> dict | None:
    """Verify a Supabase user JWT via the Auth API.

    Returns a dict with at least ``sub`` (user id) on success, or None.
    Uses the admin auth endpoint (service-role) so it works with both
    the new publishable/secret key system and legacy JWT-based keys.
    """
    if not token:
        return None
    try:
        resp = await asyncio.to_thread(
            lambda: _client.auth.get_user(token)
        )
        user = resp.user
        if user and user.id:
            return {"sub": user.id, "email": user.email}
    except Exception as exc:
        log.debug("JWT verification failed: %s", exc)
    return None


# ── Database helpers (bot_sessions table) ─────────────────────────────

async def create_session(
    user_id: str,
    bot_id: str,
    meeting_url: str,
    source_lang: str,
    target_lang: str,
) -> dict:
    """Insert a new bot_sessions row."""
    row = {
        "user_id": user_id,
        "bot_id": bot_id,
        "meeting_url": meeting_url,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "status": "in_call",
    }
    resp = await asyncio.to_thread(
        lambda: _client.table("bot_sessions").insert(row).execute()
    )
    return resp.data[0] if resp.data else row


async def update_session_status(
    bot_id: str,
    status: str,
    clip_count: int | None = None,
    duration: float | None = None,
) -> None:
    """Update a session's status (and optionally clip_count / duration)."""
    updates: dict[str, Any] = {"status": status}
    if clip_count is not None:
        updates["clip_count"] = clip_count
    if duration is not None:
        updates["duration"] = duration
    if status == "stopped":
        updates["stopped_at"] = datetime.now(timezone.utc).isoformat()
    await asyncio.to_thread(
        lambda: _client.table("bot_sessions").update(updates).eq("bot_id", bot_id).execute()
    )


async def get_user_sessions(user_id: str) -> list[dict]:
    """Return all sessions for a user, newest first."""
    resp = await asyncio.to_thread(
        lambda: (
            _client.table("bot_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    )
    return resp.data or []


async def get_session_by_bot_id(bot_id: str) -> dict | None:
    """Look up a single session by bot_id."""
    resp = await asyncio.to_thread(
        lambda: (
            _client.table("bot_sessions")
            .select("*")
            .eq("bot_id", bot_id)
            .limit(1)
            .execute()
        )
    )
    return resp.data[0] if resp.data else None


# ── Storage helpers ───────────────────────────────────────────────────

BUCKET = "recordings"


async def upload_clip(user_id: str, bot_id: str, clip_num: int, mp3_bytes: bytes) -> None:
    """Upload a single MP3 clip to Supabase Storage."""
    path = f"{user_id}/{bot_id}/clip_{clip_num:04d}.mp3"
    try:
        await asyncio.to_thread(
            lambda: _client.storage.from_(BUCKET).upload(
                path, mp3_bytes, {"content-type": "audio/mpeg"}
            )
        )
    except Exception:
        log.exception("Failed to upload clip %s", path)


async def upload_text_file(user_id: str, bot_id: str, filename: str, text: str) -> None:
    """Upload a text file (SRT, JSONL, etc.) to Supabase Storage."""
    path = f"{user_id}/{bot_id}/{filename}"
    content_type = "text/plain; charset=utf-8"
    if filename.endswith(".jsonl"):
        content_type = "application/json; charset=utf-8"
    try:
        await asyncio.to_thread(
            lambda: _client.storage.from_(BUCKET).upload(
                path, text.encode("utf-8"), {"content-type": content_type}
            )
        )
    except Exception:
        log.exception("Failed to upload text file %s", path)


async def get_signed_url(path: str, expires_in: int = 3600) -> str | None:
    """Generate a signed download URL for a storage object."""
    try:
        resp = await asyncio.to_thread(
            lambda: _client.storage.from_(BUCKET).create_signed_url(path, expires_in)
        )
        return resp.get("signedURL") or resp.get("signedUrl")
    except Exception:
        log.exception("Failed to create signed URL for %s", path)
        return None
