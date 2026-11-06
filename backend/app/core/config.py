from typing import Optional, Any
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CardioGuard AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "development-level-secret-jwt-signing-key-for-cardioguard-wearable"

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def assemble_secret_key(cls, v: Optional[str]) -> str:
        import os
        key = v or os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY")
        if isinstance(key, str) and key.strip():
            return key.strip()
        return "development-level-secret-jwt-signing-key-for-cardioguard-wearable"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PostgreSQL Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cardioguard"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: ValidationInfo) -> Any:
        import os
        import urllib.parse
        raw_url = v or os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
        if isinstance(raw_url, str) and raw_url.strip():
            url = raw_url.strip()
            # Convert standard postgres/postgresql scheme to asyncpg
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            # Clean and sanitize URL query parameters for asyncpg compatibility
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            asyncpg_params = {}
            
            # Handle SSL requirement (Neon / Supabase / AWS RDS / Render Postgres)
            if "sslmode" in query_params:
                mode = query_params["sslmode"][0]
                if mode in ["require", "verify-ca", "verify-full"]:
                    asyncpg_params["ssl"] = "require"
                elif mode == "disable":
                    pass
                else:
                    asyncpg_params["ssl"] = mode
            elif "ssl" in query_params:
                asyncpg_params["ssl"] = query_params["ssl"][0]
            elif "neon.tech" in parsed.netloc or "aws" in parsed.netloc:
                asyncpg_params["ssl"] = "require"
            
            # Whitelist parameters accepted by asyncpg (drop libpq arguments like channel_binding)
            valid_keys = {"ssl", "timeout", "command_timeout", "target_session_attrs"}
            for k, val in query_params.items():
                if k in valid_keys and k not in asyncpg_params:
                    asyncpg_params[k] = val[0]
            
            new_query = urllib.parse.urlencode(asyncpg_params)
            return urllib.parse.urlunparse(parsed._replace(query=new_query))
            
        server = values.data.get("POSTGRES_SERVER", "localhost")
        user = values.data.get("POSTGRES_USER", "postgres")
        password = values.data.get("POSTGRES_PASSWORD", "postgres")
        db = values.data.get("POSTGRES_DB", "cardioguard")
        port = values.data.get("POSTGRES_PORT", 5432)
        
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # Redis Cache Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URI: Optional[str] = None

    @field_validator("REDIS_URI", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], values: ValidationInfo) -> Any:
        import os
        r_url = v or os.environ.get("REDIS_URI") or os.environ.get("REDIS_URL")
        if isinstance(r_url, str) and r_url.strip():
            return r_url.strip()
        data = values.data
        host = data.get("REDIS_HOST", "localhost")
        port = data.get("REDIS_PORT", 6379)
        return f"redis://{host}:{port}/0"

    # Firebase Administration
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    APP_CHECK_ENABLED: bool = True

    # Health Connect Client configuration
    HEALTH_CONNECT_CLIENT_ID: str = "com.cardioguard.app"
    PREDICTION_MODE: str = "demo"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
