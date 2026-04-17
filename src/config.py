import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env first (project-specific), then fall back to claudeclaw .env
local_env = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=local_env)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Claude runs via CLI — no API key needed

# Groq (Whisper STT for voice messages)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Admin notifications
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# ElevenLabs voice cloning
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")

# Limits
FREE_ANALYSES_LIMIT = int(os.getenv("FREE_ANALYSES_LIMIT", "3"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
