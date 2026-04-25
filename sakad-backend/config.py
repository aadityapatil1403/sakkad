from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    CLIP_MODEL_NAME: str = "Marqo/marqo-fashionSigLIP"
    TAXONOMY_EMBEDDING_MODEL: str = "Marqo/marqo-fashionSigLIP"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_FALLBACK_MODELS: str = ""
    GEMINI_IMAGE_MODEL: str = "gemini-3.1-flash-image-preview"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
