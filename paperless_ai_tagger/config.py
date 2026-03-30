from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    paperless_url: str
    paperless_api_token: str

    claude_model: str = "sonnet"
    processed_tag: str = "processed-by-ai"
    mode: str = "merge"
    poll_interval: int = 300
    log_level: str = "info"
    dry_run: bool = False
    batch_size: int = 10
    batch_delay: int = 5
    classify_title: bool = True
    classify_tags: bool = True
    classify_correspondent: bool = True
    classify_document_type: bool = True
    custom_prompt: str = ""
    max_content_length: int = 50000

    # OAuth token refresh support
    claude_code_oauth_token: Optional[str] = None
    claude_code_oauth_refresh_token: Optional[str] = None

    model_config = {"env_prefix": "", "case_sensitive": False}
