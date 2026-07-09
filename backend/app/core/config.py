from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "dev"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/credittracker"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    google_client_id: str = ""
    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    session_cookie_name: str = "session"
    session_max_age_seconds: int = 7 * 24 * 60 * 60
    # "lax"/False work for local dev (frontend and backend share the plain-http
    # "localhost" site). Cross-subdomain deployments (e.g. Railway's separate
    # *.up.railway.app hosts per service, which are different sites per the
    # public suffix list) need "none"/True, since SameSite=Lax cookies are
    # never sent on cross-site fetch/XHR — only on top-level navigation.
    session_cookie_samesite: str = "lax"
    session_cookie_secure: bool = False


settings = Settings()
