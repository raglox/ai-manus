"""
Blackbox AI LLM Client
Compatible with OpenAI API format
Supports Chat, Image Generation, Video Generation, and Web Search
"""

from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
import logging
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from app.domain.models.llm import LLM, LLMResponse, StreamChunk

logger = logging.getLogger(__name__)


class BlackboxLLM(LLM):
    """
    Blackbox AI LLM Client implementation.
    
    Supports:
    - Chat models (GPT-4, Claude, DeepSeek, etc.)
    - Image generation (Flux, Stable Diffusion, etc.)
    - Video generation (Veo 2, Veo 3)
    - Web search (blackbox-search)
    
    API Base: https://api.blackbox.ai
    Compatible with OpenAI SDK
    """
    
    # Model categories
    CHAT_MODELS = {
        # OpenAI models
        "gpt-4o": "blackboxai/openai/gpt-4o",
        "gpt-4o-mini": "blackboxai/openai/gpt-4o-mini",
        "gpt-4": "blackboxai/openai/gpt-4",
        "gpt-3.5-turbo": "blackboxai/openai/gpt-3.5-turbo",
        
        # Anthropic models
        "claude-3.7-sonnet": "blackboxai/anthropic/claude-3.7-sonnet",
        "claude-3.5-sonnet": "blackboxai/anthropic/claude-3.5-sonnet",
        "claude-3-opus": "blackboxai/anthropic/claude-3-opus",
        
        # DeepSeek models
        "deepseek-chat": "blackboxai/deepseek/deepseek-chat",
        "deepseek-v3": "blackboxai/deepseek/deepseek-v3",
        
        # Google models
        "gemini-2.0-flash": "blackboxai/google/gemini-2.0-flash-exp",
        "gemini-1.5-pro": "blackboxai/google/gemini-1.5-pro",
        
        # Meta Llama models
        "llama-3.3-70b": "blackboxai/meta-llama/llama-3.3-70b-instruct",
        "llama-3.2-11b-vision": "blackboxai/meta-llama/llama-3.2-11b-vision-instruct",
        
        # Web Search
        "blackbox-search": "blackboxai/blackbox-search",
    }
    
    IMAGE_MODELS = {
        # Flux models (Black Forest Labs)
        "flux-pro": "blackboxai/black-forest-labs/flux-pro",
        "flux-1.1-pro": "blackboxai/black-forest-labs/flux-1.1-pro",
        "flux-1.1-pro-ultra": "blackboxai/black-forest-labs/flux-1.1-pro-ultra",
        "flux-dev": "blackboxai/black-forest-labs/flux-dev",
        "flux-schnell": "blackboxai/black-forest-labs/flux-schnell",
        "flux-kontext-pro": "blackboxai/black-forest-labs/flux-kontext-pro",
        
        # Stable Diffusion models
        "stable-diffusion": "blackboxai/stability-ai/stable-diffusion",
        "sdxl": "blackboxai/stability-ai/sdxl",
        "sdxl-lightning-4step": "blackboxai/bytedance/sdxl-lightning-4step",
        
        # Other image models
        "nano-banana": "blackboxai/google/nano-banana",
        "kandinsky-2.2": "blackboxai/ai-forever/kandinsky-2.2",
    }
    
    VIDEO_MODELS = {
        "veo-2": "blackboxai/google/veo-2",
        "veo-3": "blackboxai/google/veo-3",
        "veo-3-fast": "blackboxai/google/veo-3-fast",
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        Initialize Blackbox LLM client.
        
        Args:
            api_key: Blackbox API key (starts with 'sk-')
            model: Model name (will be mapped to blackboxai/provider/model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        """
        self.api_key = api_key
        self.base_url = "https://api.blackbox.ai"
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        # Initialize OpenAI client pointing to Blackbox API
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.base_url,
        )
        
        logger.info(f"Initialized Blackbox LLM with model: {model}")
    
    def _get_full_model_id(self, model: str) -> str:
        """
        Get full Blackbox model ID from short name.
        
        Args:
            model: Short model name (e.g., "gpt-4o", "flux-pro", "veo-2")
            
        Returns:
            Full model ID (e.g., "blackboxai/openai/gpt-4o")
        """
        # Check if already full ID
        if model.startswith("blackboxai/"):
            return model
        
        # Check in each category
        if model in self.CHAT_MODELS:
            return self.CHAT_MODELS[model]
        elif model in self.IMAGE_MODELS:
            return self.IMAGE_MODELS[model]
        elif model in self.VIDEO_MODELS:
            return self.VIDEO_MODELS[model]
        else:
            # Default: assume it's a chat model
            logger.warning(f"Model {model} not found in predefined models, using as-is")
            return model
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Send chat completion request to Blackbox API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)
        
        Returns:
            LLMResponse object with response text and metadata
        """
        try:
            # Get model from kwargs or use default
            model = kwargs.pop("model", self.model)
            full_model_id = self._get_full_model_id(model)
            
            # Merge parameters
            params = {
                "model": full_model_id,
                "messages": messages,
                "temperature": kwargs.pop("temperature", self.temperature),
                "max_tokens": kwargs.pop("max_tokens", self.max_tokens),
                **kwargs,
                **self.kwargs,
            }
            
            if stream:
                # Streaming not supported in synchronous response
                raise NotImplementedError("Use stream_chat() for streaming responses")
            
            logger.info(f"Sending chat request to Blackbox API with model: {full_model_id}")
            
            # Make request
            response: ChatCompletion = await self.client.chat.completions.create(**params)
            
            # Extract response
            content = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason or "stop"
            
            # Check if this is an image/video generation response
            # (Blackbox returns URL in content)
            is_generation = model in self.IMAGE_MODELS or model in self.VIDEO_MODELS
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                finish_reason=finish_reason,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )
            
        except Exception as e:
            logger.error(f"Error in Blackbox chat: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream chat completion from Blackbox API.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Yields:
            StreamChunk objects with delta content
        """
        try:
            # Get model from kwargs or use default
            model = kwargs.pop("model", self.model)
            full_model_id = self._get_full_model_id(model)
            
            # Merge parameters
            params = {
                "model": full_model_id,
                "messages": messages,
                "temperature": kwargs.pop("temperature", self.temperature),
                "max_tokens": kwargs.pop("max_tokens", self.max_tokens),
                "stream": True,
                **kwargs,
                **self.kwargs,
            }
            
            logger.info(f"Streaming chat from Blackbox API with model: {full_model_id}")
            
            # Stream response
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                chunk: ChatCompletionChunk
                
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    if delta.content:
                        yield StreamChunk(
                            delta=delta.content,
                            finish_reason=chunk.choices[0].finish_reason,
                        )
                        
        except Exception as e:
            logger.error(f"Error in Blackbox stream_chat: {e}")
            raise
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "flux-pro",
        **kwargs
    ) -> str:
        """
        Generate an image using Blackbox image models.
        
        Args:
            prompt: Text description of the image to generate
            model: Image model to use (default: "flux-pro")
            **kwargs: Additional parameters
            
        Returns:
            URL of the generated image
        """
        try:
            full_model_id = self._get_full_model_id(model)
            
            logger.info(f"Generating image with model: {full_model_id}")
            
            # Use chat completions API for image generation
            response = await self.client.chat.completions.create(
                model=full_model_id,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            
            # Blackbox returns the image URL in the content
            image_url = response.choices[0].message.content
            
            logger.info(f"Generated image URL: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise
    
    async def generate_video(
        self,
        prompt: str,
        model: str = "veo-2",
        **kwargs
    ) -> str:
        """
        Generate a video using Blackbox video models.
        
        Args:
            prompt: Text description of the video to generate
            model: Video model to use (default: "veo-2")
            **kwargs: Additional parameters
            
        Returns:
            URL of the generated video
        """
        try:
            full_model_id = self._get_full_model_id(model)
            
            logger.info(f"Generating video with model: {full_model_id}")
            
            # Use chat completions API for video generation
            response = await self.client.chat.completions.create(
                model=full_model_id,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            
            # Blackbox returns the video URL in the content
            video_url = response.choices[0].message.content
            
            logger.info(f"Generated video URL: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            raise
    
    async def web_search(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform web search using Blackbox search model.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            Dict with response content and source citations
        """
        try:
            logger.info(f"Performing web search: {query}")
            
            # Use blackbox-search model
            response = await self.client.chat.completions.create(
                model="blackboxai/blackbox-search",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides accurate, up-to-date information."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                **kwargs
            )
            
            content = response.choices[0].message.content
            
            # Extract source citations from annotations
            sources = []
            if hasattr(response.choices[0].message, 'annotations'):
                for annotation in response.choices[0].message.annotations:
                    if annotation.type == 'url_citation':
                        sources.append({
                            "title": annotation.url_citation.title,
                            "url": annotation.url_citation.url
                        })
            
            return {
                "content": content,
                "sources": sources,
                "model": response.model,
            }
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            raise
    
    async def close(self):
        """Close the client connection."""
        try:
            await self.client.close()
            logger.info("Closed Blackbox LLM client")
        except Exception as e:
            logger.error(f"Error closing Blackbox client: {e}")
