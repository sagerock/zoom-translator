import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# API keys
RECALL_API_KEY = os.environ["RECALL_API_KEY"]
DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Server
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
WEBSOCKET_PORT = int(os.getenv("PORT", os.getenv("WEBSOCKET_PORT", "8765")))

# Translation defaults
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")

# Supported languages: mapping from Deepgram language codes to DeepL target codes
LANGUAGE_MAP = {
    "en": "EN-US",
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "pt": "PT-BR",
    "ja": "JA",
    "zh": "ZH-HANS",
}

# Per-participant language overrides: participant_id -> target language code
# Populated at runtime or via config. Participants not listed get TARGET_LANGUAGE.
PARTICIPANT_LANGUAGES: dict[str, str] = {}

# OpenAI TTS voice per target language
TTS_VOICES = {
    "en": "alloy",
    "es": "nova",
    "fr": "nova",
    "de": "onyx",
    "pt": "nova",
    "ja": "nova",
    "zh": "nova",
}

RECALL_API_BASE = "https://eu-central-1.recall.ai/api/v1"
