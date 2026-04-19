from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_HOURS: int = 24
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    GEMINI_API_KEY: str


settings = Settings()