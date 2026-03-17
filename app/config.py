from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "SecondMe"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./secondme.db"

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # WeChat Config
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_redirect_uri: str = ""

    # AI Model (Minimax compatible with OpenAI API)
    openai_api_base: str = ""
    openai_api_key: str = ""
    openai_model: str = "default-model"

    # MiniMax Embedding
    minimax_group_id: str = ""
    minimax_api_key: str = ""

    # Agent Config
    agent_conversation_rounds: int = 5  # Number of conversation rounds before calculating heart score
    daily_quota_limit: int = 5  # Daily conversation quota for normal users

    class Config:
        env_file = ".env"


settings = Settings()
