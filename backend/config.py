from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Groq
    GROQ_API_KEY: str

    # App
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


# Single instance used across the entire app
# Everyone imports this one object — never create Settings() twice
settings = Settings()