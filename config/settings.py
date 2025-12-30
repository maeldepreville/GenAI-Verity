import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import boto3
from dotenv import load_dotenv
from requests_aws4auth import AWS4Auth


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class AppConfig:
    log_level: str
    enable_logging: bool
    max_upload_size_mb: int
    chunk_size: int
    chunk_overlap: int


@dataclass(frozen=True)
class AWSConfig:
    aws_auth: AWS4Auth
    region: str
    service: str
    opsearch_endpoint: str
    index_name: str


class Settings:
    _instance: Optional["Settings"] = None
    _initialized: bool

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._load_env_file()
        self.gemini: GeminiConfig = self._load_gemini_config()
        self.app: AppConfig = self._load_app_config()
        self._configure_logging()

        self._initialized = True

    def _load_env_file(self) -> None:
        env_path = Path(__file__).parent / ".env"

        if not env_path.exists():
            env_path = Path(__file__).parent.parent / ".env"

        if env_path.exists():
            load_dotenv(env_path)
        else:
            logging.warning(".env file not found at %s", env_path)

    def _aws_credentials(self) -> AWSConfig:
        region = os.getenv("AWS_REGION", "eu-north-1")
        service = os.getenv("AWS_SERVICE", "aoss")

        session = boto3.Session()
        credentials = session.get_credentials()

        if credentials is None:
            raise RuntimeError("AWS credentials not found")

        frozen_creds = credentials.get_frozen_credentials()

        aws_auth = AWS4Auth(
            frozen_creds.access_key,
            frozen_creds.secret_key,
            region,
            service,
            session_token=frozen_creds.token,
        )

        return AWSConfig(
            aws_auth=aws_auth,
            region=region,
            service=service,
            opsearch_endpoint=os.getenv(
                "OPENSEARCH_ENDPOINT",
                "https://shiwgcebosoddurpv2be.eu-north-1.aoss.amazonaws.com",
            ),
            index_name=os.getenv("INDEX_NAME", "index-gemini"),
        )

    def _load_gemini_config(self) -> GeminiConfig:
        api_key = os.getenv("GOOGLE_API_KEY", "")

        if not api_key or api_key.startswith("your_"):
            raise ValueError("GOOGLE_API_KEY not configured in .env file")

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.0"))
        max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", "8192"))

        return GeminiConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _load_app_config(self) -> AppConfig:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        enable_logging = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
        max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
        chunk_size = int(os.getenv("CHUNK_SIZE", "4000"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

        return AppConfig(
            log_level=log_level,
            enable_logging=enable_logging,
            max_upload_size_mb=max_upload_size_mb,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _configure_logging(self) -> None:
        if not self.app.enable_logging:
            return

        log_level = getattr(
            logging,
            self.app.log_level.upper(),
            logging.INFO,
        )

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def get_settings() -> Settings:
    return Settings()
