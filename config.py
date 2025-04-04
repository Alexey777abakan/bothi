import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки OpenRouter API
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Модели для генерации текста
PRIMARY_MODEL = "google/gemini-2.5-pro-exp-03-25:free"
BACKUP_MODEL = "deepseek/deepseek-chat-v3-0324:free"
LAST_RESORT_MODEL = "openai/gpt-4o-mini:free"

# Максимальная длина промпта
MAX_PROMPT_LENGTH = 4000

# Максимальная длина генерируемого текста
MAX_TOKENS = 1000

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TEST_CHANNEL_ID = os.getenv("TELEGRAM_CHAT_ID", "@tesisori")
EXCEL_FILE_PATH = "telegram_bot_data.db"  # Упрощенный путь для SQLite, будет создан в текущей директории
MAX_CAPTION_LENGTH = 1024
MAX_POST_LENGTH = 950
IMGUR_CLIENT_ID = "ec196cbda352060"
