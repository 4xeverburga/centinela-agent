from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    bot_http_api_token: str = Field(alias="BOT_HTTP_API_TOKEN")
    telegram_bot_user_id: str = Field(alias="TELEGRAM_BOT_USER_ID")
    telegram_bot_display_name: str = Field(alias="TELEGRAM_BOT_DISPLAY_NAME")

    # vLLM / LLM
    vllm_base_url: str = Field(alias="VLLM_BASE_URL")
    vllm_model: str = Field(alias="VLLM_MODEL")

    # Hugging Face (needed on the droplet to download gated weights)
    hf_token: str = Field(alias="HF_TOKEN")

    # AMD droplet (for SSH/ops reference; not used at runtime)
    droplet_ip: str = Field(alias="DROPLET_IP")
    droplet_ssh_prv_key_path: str = Field(alias="DROPLET_SSH_PRV_KEY_PATH")

    # Database
    sqlite_path: str = Field(alias="SQLITE_PATH")

    # Image pipeline
    embedding_backend: str = Field(alias="EMBEDDING_BACKEND")  # "imagehash" | "clip"
    image_jpeg_quality: int = Field(alias="IMAGE_JPEG_QUALITY")
    image_max_long_edge: int = Field(alias="IMAGE_MAX_LONG_EDGE")
    image_sharpness_min: float = Field(alias="IMAGE_SHARPNESS_MIN")
    image_similarity_threshold: float = Field(alias="IMAGE_SIMILARITY_THRESHOLD")
    # Window in seconds within which incoming photos are clustered together
    clustering_window_seconds: int = Field(alias="CLUSTERING_WINDOW_SECONDS")

    # Queue worker
    worker_max_attempts: int = Field(alias="WORKER_MAX_ATTEMPTS")
    worker_backoff_base_seconds: float = Field(alias="WORKER_BACKOFF_BASE_SECONDS")

    # Project lifecycle
    project_auto_close_hours: int = Field(alias="PROJECT_AUTO_CLOSE_HOURS")

    # HITL
    hitl_context_max_messages: int = Field(alias="HITL_CONTEXT_MAX_MESSAGES")
    hitl_context_window_minutes: int = Field(alias="HITL_CONTEXT_WINDOW_MINUTES")
