"""
Configuración centralizada leída desde variables de entorno.

Adopta el patrón de u_05_v2: variables individuales de PostgreSQL
con @computed_field para construir DATABASE_URL automáticamente.
Los valores sensibles (SECRET_KEY, POSTGRES_PASSWORD) viven en .env.
"""

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ─── Base de datos (PostgreSQL — patrón u_05_v2) ──────────────────────────
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/foodstore_db"

    # ─── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM:  str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ─── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = []


    FRONTEND_URL: str

    # ─── Mercado Pago ─────────────────────────────────────────────────────────
    MP_ACCESS_TOKEN: str
    MP_NOTIFICATION_URL: str = ""
    MP_WEBHOOK_URL: str = ""

   # ─── Cloudinary ───────────────────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    model_config = {
        "env_file":          ".env",
        "env_file_encoding": "utf-8",
        "extra":             "ignore",
    }
    print("CORS_ORIGINS:", CORS_ORIGINS)



settings = Settings()
