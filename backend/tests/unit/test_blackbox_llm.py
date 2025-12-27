"""
Tests for Blackbox AI LLM Client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.infrastructure.external.llm.blackbox_llm import BlackboxLLM


@pytest.fixture
def blackbox_client():
    """Create a Blackbox LLM client for testing."""
    return BlackboxLLM(
        api_key="sk-test-key",
        model="gpt-4o",
        temperature=0.7,
        max_tokens=100,
    )


class TestBlackboxLLM:
    """Test Blackbox LLM client."""
    
    def test_initialization(self, blackbox_client):
        """Test that Blackbox client initializes correctly."""
        assert blackbox_client.api_key == "sk-test-key"
        assert blackbox_client.base_url == "https://api.blackbox.ai"
        assert blackbox_client.model == "gpt-4o"
        assert blackbox_client.temperature == 0.7
        assert blackbox_client.max_tokens == 100
    
    def test_get_full_model_id_chat(self, blackbox_client):
        """Test getting full model ID for chat models."""
        # Test predefined model
        assert blackbox_client._get_full_model_id("gpt-4o") == "blackboxai/openai/gpt-4o"
        assert blackbox_client._get_full_model_id("claude-3.5-sonnet") == "blackboxai/anthropic/claude-3.5-sonnet"
        assert blackbox_client._get_full_model_id("deepseek-chat") == "blackboxai/deepseek/deepseek-chat"
        
        # Test already full ID
        assert blackbox_client._get_full_model_id("blackboxai/openai/gpt-4o") == "blackboxai/openai/gpt-4o"
    
    def test_get_full_model_id_image(self, blackbox_client):
        """Test getting full model ID for image models."""
        assert blackbox_client._get_full_model_id("flux-pro") == "blackboxai/black-forest-labs/flux-pro"
        assert blackbox_client._get_full_model_id("stable-diffusion") == "blackboxai/stability-ai/stable-diffusion"
        assert blackbox_client._get_full_model_id("sdxl") == "blackboxai/stability-ai/sdxl"
    
    def test_get_full_model_id_video(self, blackbox_client):
        """Test getting full model ID for video models."""
        assert blackbox_client._get_full_model_id("veo-2") == "blackboxai/google/veo-2"
        assert blackbox_client._get_full_model_id("veo-3") == "blackboxai/google/veo-3"
        assert blackbox_client._get_full_model_id("veo-3-fast") == "blackboxai/google/veo-3-fast"
    
    @pytest.mark.asyncio
    async def test_chat_success(self, blackbox_client):
        """Test successful chat completion."""
        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I'm Blackbox AI."
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "blackboxai/openai/gpt-4o"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model_dump = lambda: {"test": "data"}
        
        with patch.object(blackbox_client.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            response = await blackbox_client.chat(
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            assert response.content == "Hello! I'm Blackbox AI."
            assert response.model == "blackboxai/openai/gpt-4o"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 5
            assert response.usage["total_tokens"] == 15
            assert response.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_image(self, blackbox_client):
        """Test image generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "https://example.com/image.png"
        
        with patch.object(blackbox_client.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            image_url = await blackbox_client.generate_image(
                prompt="A futuristic cityscape",
                model="flux-pro"
            )
            
            assert image_url == "https://example.com/image.png"
    
    @pytest.mark.asyncio
    async def test_generate_video(self, blackbox_client):
        """Test video generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "https://example.com/video.mp4"
        
        with patch.object(blackbox_client.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            video_url = await blackbox_client.generate_video(
                prompt="A car driving on highway",
                model="veo-2"
            )
            
            assert video_url == "https://example.com/video.mp4"
    
    @pytest.mark.asyncio
    async def test_web_search(self, blackbox_client):
        """Test web search functionality."""
        # Mock response with annotations
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Latest AI news..."
        mock_response.choices[0].message.annotations = [
            MagicMock(
                type='url_citation',
                url_citation=MagicMock(
                    title="AI News",
                    url="https://example.com/news"
                )
            )
        ]
        mock_response.model = "blackboxai/blackbox-search"
        
        with patch.object(blackbox_client.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await blackbox_client.web_search(
                query="What are the latest AI developments?"
            )
            
            assert result["content"] == "Latest AI news..."
            assert len(result["sources"]) == 1
            assert result["sources"][0]["title"] == "AI News"
            assert result["sources"][0]["url"] == "https://example.com/news"
            assert result["model"] == "blackboxai/blackbox-search"
    
    @pytest.mark.asyncio
    async def test_close(self, blackbox_client):
        """Test closing the client."""
        with patch.object(blackbox_client.client, 'close', new=AsyncMock()) as mock_close:
            await blackbox_client.close()
            mock_close.assert_called_once()


class TestModelCategories:
    """Test model categories and mappings."""
    
    def test_chat_models(self):
        """Test that all chat models are properly defined."""
        assert "gpt-4o" in BlackboxLLM.CHAT_MODELS
        assert "claude-3.5-sonnet" in BlackboxLLM.CHAT_MODELS
        assert "deepseek-chat" in BlackboxLLM.CHAT_MODELS
        assert "gemini-2.0-flash" in BlackboxLLM.CHAT_MODELS
        assert "blackbox-search" in BlackboxLLM.CHAT_MODELS
    
    def test_image_models(self):
        """Test that all image models are properly defined."""
        assert "flux-pro" in BlackboxLLM.IMAGE_MODELS
        assert "stable-diffusion" in BlackboxLLM.IMAGE_MODELS
        assert "sdxl" in BlackboxLLM.IMAGE_MODELS
    
    def test_video_models(self):
        """Test that all video models are properly defined."""
        assert "veo-2" in BlackboxLLM.VIDEO_MODELS
        assert "veo-3" in BlackboxLLM.VIDEO_MODELS
        assert "veo-3-fast" in BlackboxLLM.VIDEO_MODELS
