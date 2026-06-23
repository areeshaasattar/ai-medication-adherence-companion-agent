import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",         
        case_sensitive=True
    )

    PROJECT_NAME: str = "AI Medication Adherence Companion"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        if "?" in url:
            base_url, query = url.split("?", 1)
            params = query.split("&")
            filtered_params = [p for p in params if not p.startswith("sslmode=") and not p.startswith("channel_binding=")]
            if filtered_params:
                url = f"{base_url}?{'&'.join(filtered_params)}"
            else:
                url = base_url
        return url

    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = "your-openai-api-key"
    
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  

settings = Settings()

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY