from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Productivity Tracker API"
    APP_ENV: str = "dev"
    APP_PORT: int = 8000

    DATABASE_URL: str

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_API_BASE: str = "https://api.telegram.org"

    USER_CHAT_ID: str = ""

    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_SECONDS: int = 60
    SCHEDULER_TIMEZONE: str = "Asia/Jakarta"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()