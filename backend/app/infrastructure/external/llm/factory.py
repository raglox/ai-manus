"""
LLM Factory - Creates LLM instances based on configuration
"""

from typing import Optional
import logging

from app.core.config import get_settings
from app.domain.models.llm import LLM
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.llm.blackbox_llm import BlackboxLLM

logger = logging.getLogger(__name__)


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLM:
    """
    Factory function to create LLM client based on configuration.
    
    Args:
        provider: LLM provider name ("deepseek", "blackbox", "openai", None=auto)
        model: Model name (optional, uses config default)
        **kwargs: Additional parameters for the LLM client
        
    Returns:
        LLM instance
        
    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    settings = get_settings()
    
    # Determine provider
    if provider is None:
        provider = settings.llm_provider.lower()
    
    # Get model name
    if model is None:
        model = settings.model_name
    
    logger.info(f"Creating LLM client: provider={provider}, model={model}")
    
    # Create client based on provider
    if provider == "blackbox":
        # Blackbox AI
        api_key = settings.blackbox_api_key or settings.api_key
        if not api_key:
            raise ValueError(
                "Blackbox API key is required. "
                "Set BLACKBOX_API_KEY or API_KEY environment variable."
            )
        
        return BlackboxLLM(
            api_key=api_key,
            model=model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            **kwargs
        )
    
    elif provider in ["deepseek", "openai"]:
        # DeepSeek or OpenAI (both use OpenAI-compatible API)
        api_key = settings.api_key
        if not api_key:
            raise ValueError(
                f"{provider.upper()} API key is required. "
                f"Set API_KEY environment variable."
            )
        
        # Determine base URL
        if provider == "deepseek":
            api_base = "https://api.deepseek.com/v1"
        else:  # openai
            api_base = "https://api.openai.com/v1"
        
        return OpenAILLM(
            api_key=api_key,
            base_url=api_base,
            model=model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            **kwargs
        )
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: deepseek, blackbox, openai"
        )


async def test_llm_connection(provider: Optional[str] = None) -> bool:
    """
    Test LLM connection.
    
    Args:
        provider: LLM provider to test (None=use config default)
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        llm = get_llm_client(provider=provider)
        
        # Test with a simple message
        response = await llm.chat(
            messages=[
                {"role": "user", "content": "Hello! Please respond with 'OK' if you can read this."}
            ],
            max_tokens=10
        )
        
        await llm.close()
        
        logger.info(f"LLM connection test successful: {response.content[:50]}")
        return True
        
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        return False
