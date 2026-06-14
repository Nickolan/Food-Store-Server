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
    postgres_user:     str = "postgres"
    postgres_password: str = "tutuca05"
    postgres_db:       str = "db_parcial_python"
    postgres_host:     str = "localhost"
    postgres_port:     int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Construye la URL de conexión a PostgreSQL.
        Para tests se sobreescribe con SQLite en memoria desde conftest.py.
        """
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ─── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM:  str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ─── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = []


    FRONTEND_URL: str

    # ─── Mercado Pago ─────────────────────────────────────────────────────────
    MP_ACCESS_TOKEN: str
    MP_WEBHOOK_SECRET: str
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
