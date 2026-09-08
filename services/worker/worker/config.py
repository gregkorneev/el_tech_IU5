from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./elteh.sqlite3"
    yandex_public_key: str = "https://disk.yandex.ru/d/Ec-K9jdIgGalFg"
    sync_interval_hours: int = 24
    transcription_provider: str = "faster_whisper"
    transcription_model: str = "base"


settings = Settings()
