"""OpenAI TTS — converts translated text to MP3 audio bytes."""

from __future__ import annotations

import base64
import logging

from openai import AsyncOpenAI

import config

log = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def synthesize(text: str, lang: str) -> str:
    """Convert *text* to speech and return base64-encoded MP3.

    Args:
        text: Text to speak.
        lang: 2-letter target language code, used to pick a voice.

    Returns:
        Base64-encoded MP3 audio string.
    """
    voice = config.TTS_VOICES.get(lang, "alloy")

    response = await _client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )

    mp3_bytes = response.content
    encoded = base64.b64encode(mp3_bytes).decode()
    log.info("TTS: %d chars → %d bytes MP3 (voice=%s)", len(text), len(mp3_bytes), voice)
    return encoded
