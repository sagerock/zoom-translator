# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Server

```bash
# Install dependencies (Python 3.12)
pip install -r requirements.txt

# Run locally
python server.py
```

Requires a `.env` file with: `RECALL_API_KEY`, `DEEPGRAM_API_KEY`, `DEEPL_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`. Optional: `WEBSOCKET_HOST` (default 0.0.0.0), `PORT` (default 8765), `PUBLIC_WSS_URL`, `TARGET_LANGUAGE` (default "en").

Deployed on Railway via `Procfile` (`web: python server.py`). Supabase project hosts auth, database (`bot_sessions` table with RLS), and storage (`recordings` bucket).

## Architecture

Real-time Zoom meeting translator: Recall.ai bots capture per-participant audio → server runs ASR/translate/TTS pipeline → broadcasts translated audio to listener browsers and stores recordings in Supabase.

### Data Flow per Utterance

```
Recall.ai bot → PCM audio via WebSocket
  → pipeline/asr.py (Deepgram streaming STT)
  → pipeline/translator.py (DeepL HTTP API)
  → pipeline/tts.py (OpenAI TTS → base64 MP3)
  → broadcast to /listen WebSocket clients
  → upload clip to Supabase Storage (fire-and-forget)
```

### WebSocket Routes (server.py)

- **`/mgmt?token=<JWT>`** — Management UI. Authenticated. Sends bot status updates, receives start/stop actions. Scoped per user via `mgmt_clients: dict[ws, user_id]`.
- **`/listen?lang=<code>`** — Listener browsers. No auth. Receives translated audio broadcasts.
- **Default path** — Recall.ai bot connections. Receives PCM audio events, routes to per-participant ASR streams.

### HTTP Routes (server.py `process_request`)

- `GET /` — Management HTML (with Supabase config injected via `__SUPABASE_URL__`/`__SUPABASE_ANON_KEY__` placeholders)
- `GET /listen` — Listener HTML (public, no auth)
- `GET /api/recordings` — User's sessions from DB (JWT in Authorization header)
- `GET /api/recordings/<bot_id>/audio` — Signed URLs for all clips
- `GET /recordings/<bot_id>/<file>` — 302 redirect to signed URL

### Key State

`BotSession` dataclass holds per-bot state: ASR streams (per participant), in-memory SRT/transcript buffers, clip count, audio offset for timing. Sessions stored in `bot_sessions: dict[bot_id, BotSession]`.

## Important Patterns

- **Supabase keys**: Uses new `sb_publishable_`/`sb_secret_` format. JWT verification uses `_client.auth.get_user(token)` API call, NOT local PyJWT decoding.
- **Async wrapping**: All Supabase SDK calls wrapped in `asyncio.to_thread()` to avoid blocking the event loop.
- **Fire-and-forget**: Clip uploads and DB updates use `asyncio.create_task()` — non-blocking.
- **HTML in Python strings**: `web_ui.py` exports `HTML_PAGE` and `LISTEN_PAGE` as triple-quoted strings. Use `\\x27` for JS single-quote escapes (Python `\'` becomes `'`, breaking JS).
- **CSS display gotcha**: `#main-app` has `display: none` in CSS. Must set `.style.display = "block"` to show it (not `""` which falls back to CSS rule).
- **Auth state**: `onAuthStateChange` is the single source of truth — don't also call `getSession()` or you get race conditions.
- **Storage paths**: `recordings/{user_id}/{bot_id}/clip_NNNN.mp3`, `subtitles.srt`, `transcript.jsonl`

## Future Work

### Video-synced audio and subtitles
Currently, clips are concatenated back-to-back with no gaps, and SRT timestamps match that concatenated audio. To sync translations with the original meeting video recording:
- The `elapsed` field in `transcript.jsonl` already captures wall-clock seconds since the bot joined — this is the data needed.
- Generate SRT with `elapsed`-based timestamps instead of concatenated audio offsets.
- Build audio with silence gaps inserted between clips to match real timing (ffmpeg can do this).
- This is a post-processing step — no changes to the recording pipeline needed.
