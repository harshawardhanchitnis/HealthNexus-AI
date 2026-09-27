import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    storage: str = os.getenv("HEALTHNEXUS_STORAGE", "local")
    project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "HEALTHNEXUS_CORS_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200"
        ).split(",") if origin.strip()
    )

