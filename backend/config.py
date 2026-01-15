"""
Configuration module for backend services.
Loads environment variables and provides centralized configuration.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # =========================================================================
    # DATABASE CONFIGURATION
    # =========================================================================
    MONGODB_CONNECTION_STRING: str = os.getenv(
        "MONGODB_CONNECTION_STRING",
        "mongodb://admin:password@mongodb:27017"
    )
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "blog-data")
    
    # =========================================================================
    # KAFKA CONFIGURATION
    # =========================================================================
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "coinmarketcap-news")
    
    # =========================================================================
    # API KEYS (REQUIRED)
    # =========================================================================
    # LLM API - Support both Gemini (recommended) and Together AI
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "together"
    
    # Multiple Gemini keys for rotation (comma-separated)
    _gemini_keys_str: Optional[str] = os.getenv("GEMINI_API_KEYS")
    GEMINI_API_KEYS: list = (
        [key.strip() for key in _gemini_keys_str.split(",") if key.strip()]
        if _gemini_keys_str
        else ([os.getenv("GEMINI_API_KEY")] if os.getenv("GEMINI_API_KEY") else [])
    )
    
    # Legacy single key support (backward compatible)
    GEMINI_API_KEY: Optional[str] = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None
    
    TOGETHER_API_KEY: Optional[str] = os.getenv("TOGETHER_API_KEY")
    
    # Bitcoin price data
    COINRANKING_API_KEY: Optional[str] = os.getenv("COINRANKING_API_KEY")
    
    # =========================================================================
    # OPTIONAL INTEGRATIONS
    # =========================================================================
    DISCORD_WEBHOOK_URL_ERROR: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL_ERROR")
    DISCORD_WEBHOOK_URL_SUCCESS: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL_SUCCESS")
    
    # =========================================================================
    # API CONFIGURATION
    # =========================================================================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # =========================================================================
    # ENVIRONMENT
    # =========================================================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        Raises ValueError if any required config is missing.
        """
        # Check LLM API key based on provider
        if cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEYS:
            raise ValueError(
                "GEMINI_API_KEY or GEMINI_API_KEYS is required when LLM_PROVIDER=gemini. \n"
                "Single key: GEMINI_API_KEY=your_key\n"
                "Multiple keys: GEMINI_API_KEYS=key1,key2,key3\n"
                "Get your free API key at: https://makersuite.google.com/app/apikey"
            )
        elif cls.LLM_PROVIDER == "together" and not cls.TOGETHER_API_KEY:
            raise ValueError(
                "TOGETHER_API_KEY is required when LLM_PROVIDER=together. "
                "Get your API key at: https://api.together.xyz/"
            )
        
        # Check required APIs
        if not cls.COINRANKING_API_KEY:
            raise ValueError(
                "COINRANKING_API_KEY is required. "
                "Get your free API key at: https://developers.coinranking.com/"
            )
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get a summary of current configuration (without sensitive data)."""
        return {
            "environment": cls.ENVIRONMENT,
            "mongodb_database": cls.MONGODB_DATABASE,
            "kafka_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "kafka_topic": cls.KAFKA_TOPIC,
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "llm_provider": cls.LLM_PROVIDER,
            "gemini_api_keys_count": len(cls.GEMINI_API_KEYS),
            "together_api_key_set": bool(cls.TOGETHER_API_KEY),
            "coinranking_api_key_set": bool(cls.COINRANKING_API_KEY),
            "discord_webhooks_configured": bool(cls.DISCORD_WEBHOOK_URL_ERROR),
        }


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    if Config.ENVIRONMENT != "development":
        raise
    else:
        print(f"⚠️  Configuration Warning: {e}")
        print("   Continuing in development mode, but some features may not work.")


# Export singleton config instance
config = Config()

