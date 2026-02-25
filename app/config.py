from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_SYNC: str = ""
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    APP_NAME: str = "Empireo Brain"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: list[str] = ["*"]

    BOOTSTRAP_TOKEN: str = ""

    OPENAI_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    GOOGLE_SERVICE_ACCOUNT_KEY: str = ""  # Path to SA JSON or inline JSON string
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""  # For webhook signature verification

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-south-1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
