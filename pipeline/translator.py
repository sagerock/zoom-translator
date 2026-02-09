"""DeepL translation module."""

from __future__ import annotations

import logging

import httpx

import config

log = logging.getLogger(__name__)

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
# Switch to "https://api.deepl.com/v2/translate" for a paid plan.


async def translate(text: str, target_lang: str, source_lang: str | None = None) -> str | None:
    """Translate *text* to *target_lang* via DeepL.

    Args:
        text: Source text.
        target_lang: 2-letter language code (e.g. "en", "es").
        source_lang: Optional source language hint. ``None`` = auto-detect.

    Returns:
        Translated string, or ``None`` if translation was skipped or failed.
    """
    deepl_target = config.LANGUAGE_MAP.get(target_lang, target_lang.upper())

    params: dict = {
        "text": [text],
        "target_lang": deepl_target,
    }
    if source_lang:
        params["source_lang"] = source_lang.upper()

    headers = {"Authorization": f"DeepL-Auth-Key {config.DEEPL_API_KEY}"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(DEEPL_API_URL, json=params, headers=headers)

    if resp.status_code != 200:
        log.error("DeepL error %s: %s", resp.status_code, resp.text)
        return None

    data = resp.json()
    translated = data["translations"][0]["text"]
    detected = data["translations"][0].get("detected_source_language", "??").lower()

    # If the detected source language already matches the target, skip.
    if detected == target_lang:
        log.info("Skipping translation — already in %s", target_lang)
        return None

    log.info("Translated (%s→%s): %s → %s", detected, target_lang, text, translated)
    return translated
