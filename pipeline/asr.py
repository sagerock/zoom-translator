"""Deepgram streaming ASR — converts PCM audio chunks to finalized text.

Uses the Deepgram SDK v5 async WebSocket API (AsyncDeepgramClient).
Each participant gets their own streaming connection.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Awaitable

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV1ResultsEvent

import config

log = logging.getLogger(__name__)


class ASRStream:
    """Wraps a single Deepgram streaming connection for one participant."""

    def __init__(self, participant_id: str, on_utterance: Callable[[str, str], Awaitable[None]]):
        """
        Args:
            participant_id: Identifier for this audio stream.
            on_utterance: async callback(participant_id, text) fired on each
                          finalized utterance.
        """
        self.participant_id = participant_id
        self._on_utterance = on_utterance
        self._dg = AsyncDeepgramClient(api_key=config.DEEPGRAM_API_KEY)
        self._socket = None
        self._ctx = None
        self._listen_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._ctx = self._dg.listen.v1.connect(
            model="nova-2",
            language="es",
            punctuate="true",
            interim_results="false",
            encoding="linear16",
            sample_rate="16000",
            channels="1",
        )
        self._socket = await self._ctx.__aenter__()

        # Register event handler for transcription results
        self._socket.on(EventType.MESSAGE, self._handle_message)
        self._socket.on(EventType.ERROR, self._handle_error)

        # Start the background listener that reads from the WebSocket
        self._listen_task = asyncio.create_task(self._socket.start_listening())
        log.info("ASR started for participant %s", self.participant_id)

    async def send_audio(self, pcm_bytes: bytes) -> None:
        """Send a chunk of S16LE PCM audio to Deepgram."""
        if self._socket:
            await self._socket.send_media(pcm_bytes)

    async def close(self) -> None:
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except (asyncio.CancelledError, Exception):
                pass
            self._listen_task = None

        if self._ctx:
            try:
                await self._ctx.__aexit__(None, None, None)
            except Exception:
                pass
            self._ctx = None
            self._socket = None

        log.info("ASR closed for participant %s", self.participant_id)

    async def _handle_message(self, message) -> None:
        if not isinstance(message, ListenV1ResultsEvent):
            return

        # Only process final results
        if not message.is_final:
            return

        try:
            alt = message.channel.alternatives[0]
        except (IndexError, AttributeError):
            return

        text = alt.transcript.strip()
        if not text:
            return

        # Detected language from alternatives
        detected_lang = "en"
        if alt.languages:
            detected_lang = alt.languages[0]
        # Normalise to 2-letter code
        if "-" in detected_lang:
            detected_lang = detected_lang.split("-")[0]

        log.info("[%s] ASR (%s): %s", self.participant_id, detected_lang, text)
        await self._on_utterance(self.participant_id, text)

    async def _handle_error(self, error) -> None:
        log.error("Deepgram error for %s: %s", self.participant_id, error)
