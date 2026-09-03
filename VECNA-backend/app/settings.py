from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def parse_origins(value: str) -> tuple[str, ...]:
    return tuple(origin.strip().rstrip("/") for origin in value.split(",") if origin.strip())


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    backend_host: str = os.getenv("JARVIS_BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("JARVIS_BACKEND_PORT", "8765"))
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_chat_model: str = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
    allowed_origins: tuple[str, ...] = parse_origins(
        os.getenv("JARVIS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:1420,http://127.0.0.1:1420")
    )
    local_actions_enabled: bool = parse_bool(os.getenv("JARVIS_LOCAL_ACTIONS_ENABLED", "false"))

    # Multi-Provider Neural Hot-Swap Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    backup_1_base_url: str = os.getenv("BACKUP_1_BASE_URL", "")
    backup_1_api_key: str = os.getenv("BACKUP_1_API_KEY", "")
    backup_1_model: str = os.getenv("BACKUP_1_MODEL", "")
    backup_2_base_url: str = os.getenv("BACKUP_2_BASE_URL", "")
    backup_2_api_key: str = os.getenv("BACKUP_2_API_KEY", "")
    backup_2_model: str = os.getenv("BACKUP_2_MODEL", "")

    # Optional Integrations
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_uid: str = os.getenv("TELEGRAM_ALLOWED_UID", "")
    gmail_address: str = os.getenv("GMAIL_ADDRESS", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")


settings = Settings()

