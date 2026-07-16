from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "Data Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/data_agent"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2000

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [
        ".txt",
        ".md",
        ".pdf",
        ".docx",
        ".csv",
        ".xlsx",
        ".json",
    ]

    # Encryption
    CRYPTO_KEY: str = ""  # base64 Fernet key; empty uses dev fallback

    # Auth (JWT + bcrypt). AUTH_ENABLED=False makes require_auth a no-op so the
    # open API surface and existing tests are unaffected; set True in production.
    AUTH_ENABLED: bool = False
    JWT_SECRET_KEY: str = ""  # empty uses an ephemeral dev secret (warned)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""  # when set + AUTH_ENABLED, seeds an admin on startup

    # Code Execution
    CODE_EXECUTOR_TYPE: str = "local"  # local or docker
    DOCKER_IMAGE: str = "python:3.11-slim"

    # Workflow / LLM execution
    SQL_EXEC_TIMEOUT: int = 30  # seconds
    MAX_SQL_ROWS: int = 500
    MULTI_TURN_MAX_TURNS: int = 10

    # Python analysis sandbox
    CODE_EXEC_TIMEOUT_MS: int = 60_000
    CODE_MAX_MEMORY_MB: int = 500
    PYTHON_MAX_TRIES: int = 5

    # Vector store (memory | chroma | elasticsearch)
    VECTOR_STORE_TYPE: str = "memory"


settings = Settings()
