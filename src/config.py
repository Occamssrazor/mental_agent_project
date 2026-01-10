import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/mental_agent")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_WEBHOOK_SECRET = os.getenv("TG_WEBHOOK_SECRET", "")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
LIGHT_MODEL = os.getenv("LIGHT_MODEL", "qwen2.5:1.5b")

MENTAL_BASE_MODEL = os.getenv("MENTAL_BASE_MODEL", "unsloth/Qwen2.5-7B-Instruct")
MENTAL_LORA_PATH = os.getenv("MENTAL_LORA_PATH", "/app/lora/grpo_lora")

DEFAULT_TIMEZONE = "Europe/Moscow"
DEFAULT_DAILY_TIME = "13:00"
DEFAULT_WEEKLY_DAY = "sun"

