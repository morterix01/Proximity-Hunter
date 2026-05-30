from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://glitch:glitch@localhost:5432/glitchhunter"
    redis_url: str = "redis://localhost:6379/0"

    firebase_credentials: str = "./firebase-service-account.json"

    scraper_api_key: str = ""
    use_proxy: bool = False
    scrape_interval_seconds: int = 900

    glitch_error_threshold: float = 60.0   # >= => "Errore Prezzo"
    glitch_super_threshold: float = 30.0   # >= => "Super Sconto"


settings = Settings()
