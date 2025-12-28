from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    
    # LLM Provider configuration
    llm_provider: str = "deepseek"  # "deepseek", "blackbox", "openai"
    api_key: str | None = None
    api_base: str = "https://api.deepseek.com/v1"
    
    # Blackbox AI configuration
    blackbox_api_key: str | None = None  # Blackbox API key
    blackbox_api_base: str = "https://api.blackbox.ai"
    
    # Model configuration
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # MongoDB configuration
    mongodb_uri: str = "mongodb://mongodb:27017"
    mongodb_database: str = "manus"
    mongodb_username: str | None = None
    mongodb_password: str | None = None
    
    # Redis configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    
    # Sandbox configuration
    sandbox_address: str | None = None
    sandbox_image: str | None = None
    sandbox_name_prefix: str | None = None
    sandbox_ttl_minutes: int | None = 30
    sandbox_network: str | None = None  # Docker network bridge name
    sandbox_chrome_args: str | None = ""
    sandbox_https_proxy: str | None = None
    sandbox_http_proxy: str | None = None
    sandbox_no_proxy: str | None = None
    
    # Search engine configuration
    search_provider: str | None = "bing"  # "baidu", "google", "bing"
    google_search_api_key: str | None = None
    google_search_engine_id: str | None = None
    
    # Auth configuration
    auth_provider: str = "password"  # "password", "none", "local"
    password_salt: str | None = None
    password_hash_rounds: int = 10
    password_hash_algorithm: str = "pbkdf2_sha256"
    local_auth_email: str = "admin@example.com"
    local_auth_password: str = "admin"
    
    # Email configuration
    email_host: str | None = None  # "smtp.gmail.com"
    email_port: int | None = None  # 587
    email_username: str | None = None
    email_password: str | None = None
    email_from: str | None = None
    
    # JWT configuration
    jwt_secret_key: str  # REQUIRED - Must be set in environment variables
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # MCP configuration
    mcp_config_path: str = "/etc/mcp.json"
    
    # Stripe billing configuration
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id_basic: str | None = None
    stripe_price_id_pro: str | None = None
    
    # Sentry error tracking configuration
    sentry_dsn: str | None = None
    sentry_environment: str = "production"
    sentry_traces_sample_rate: float = 0.1  # 10% performance monitoring
    sentry_profiles_sample_rate: float = 0.1  # 10% profiling
    
    # Logging configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def validate(self):
        """Validate configuration settings"""
        # Critical secrets validation - check based on LLM provider
        if self.llm_provider == "blackbox":
            if not self.blackbox_api_key:
                raise ValueError("Blackbox API key is required when using blackbox provider")
        elif not self.api_key:
            # For deepseek/openai/other providers
            raise ValueError(f"API key is required for provider: {self.llm_provider}")
        
        if not self.jwt_secret_key or self.jwt_secret_key == "your-secret-key-here":
            raise ValueError("JWT_SECRET_KEY must be set in environment variables. Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long for security")
        
        # Stripe validation for production
        if self.stripe_secret_key and not self.stripe_webhook_secret:
            import logging
            logging.warning("STRIPE_WEBHOOK_SECRET not set - webhook verification will fail!")
        
        # Password salt validation
        if self.auth_provider == "password" and not self.password_salt:
            import logging
            logging.warning("PASSWORD_SALT not set - using default (not recommended for production)")

@lru_cache()
def get_settings() -> Settings:
    """Get application settings"""
    settings = Settings()
    settings.validate()
    return settings 
