import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env из родительской директории claudeclaw
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))

# Anthropic/Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")

# Лимиты
FREE_ANALYSES_LIMIT = int(os.getenv("FREE_ANALYSES_LIMIT", "3"))

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
