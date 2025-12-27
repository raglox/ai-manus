# 🤖 Blackbox AI Integration Guide

**Date**: December 27, 2025  
**Status**: ✅ **Ready to Use**

---

## 📋 Overview

تم دمج **Blackbox AI** بالكامل في المشروع، مما يوفر إمكانيات متقدمة:

### ✨ Capabilities
- 💬 **Chat Models**: GPT-4, Claude, DeepSeek, Gemini, Llama
- 🎨 **Image Generation**: Flux Pro, Stable Diffusion, SDXL
- 🎥 **Video Generation**: Veo 2, Veo 3, Veo 3 Fast
- 🔍 **Web Search**: Real-time web search with citations

---

## 🚀 Quick Start

### 1. **API Key Setup**

```bash
# في .env file
BLACKBOX_API_KEY=sk-SuSCd8TN7baNnh2EcFnGzw
LLM_PROVIDER=blackbox
```

### 2. **Basic Usage**

```python
from app.infrastructure.external.llm.blackbox_llm import BlackboxLLM

# إنشاء Client
llm = BlackboxLLM(
    api_key="sk-SuSCd8TN7baNnh2EcFnGzw",
    model="gpt-4o",
    temperature=0.7,
)

# Chat
response = await llm.chat(
    messages=[
        {"role": "user", "content": "مرحباً!"}
    ]
)
print(response.content)
```

---

## 🎯 Available Models

### 💬 Chat Models

| Model Short Name | Full Model ID | Provider | Context Length |
|------------------|---------------|----------|----------------|
| `gpt-4o` | `blackboxai/openai/gpt-4o` | OpenAI | 128K |
| `gpt-4o-mini` | `blackboxai/openai/gpt-4o-mini` | OpenAI | 128K |
| `claude-3.7-sonnet` | `blackboxai/anthropic/claude-3.7-sonnet` | Anthropic | 200K |
| `claude-3.5-sonnet` | `blackboxai/anthropic/claude-3.5-sonnet` | Anthropic | 200K |
| `deepseek-chat` | `blackboxai/deepseek/deepseek-chat` | DeepSeek | 64K |
| `deepseek-v3` | `blackboxai/deepseek/deepseek-v3` | DeepSeek | 64K |
| `gemini-2.0-flash` | `blackboxai/google/gemini-2.0-flash-exp` | Google | 1M |
| `llama-3.3-70b` | `blackboxai/meta-llama/llama-3.3-70b-instruct` | Meta | 128K |
| `llama-3.2-11b-vision` | `blackboxai/meta-llama/llama-3.2-11b-vision-instruct` | Meta | 128K |
| `blackbox-search` | `blackboxai/blackbox-search` | Blackbox | - |

**Usage**:
```python
# يمكنك استخدام الاسم المختصر
response = await llm.chat(messages=[...], model="gpt-4o")

# أو Full ID
response = await llm.chat(messages=[...], model="blackboxai/openai/gpt-4o")
```

---

### 🎨 Image Generation Models

| Model Short Name | Full Model ID | Cost per Image | Quality |
|------------------|---------------|----------------|---------|
| `flux-pro` | `blackboxai/black-forest-labs/flux-pro` | $0.055 | ⭐⭐⭐⭐⭐ |
| `flux-1.1-pro` | `blackboxai/black-forest-labs/flux-1.1-pro` | $0.040 | ⭐⭐⭐⭐⭐ |
| `flux-1.1-pro-ultra` | `blackboxai/black-forest-labs/flux-1.1-pro-ultra` | $0.060 | ⭐⭐⭐⭐⭐ |
| `flux-dev` | `blackboxai/black-forest-labs/flux-dev` | $0.025 | ⭐⭐⭐⭐ |
| `flux-schnell` | `blackboxai/black-forest-labs/flux-schnell` | $0.003 | ⭐⭐⭐ |
| `stable-diffusion` | `blackboxai/stability-ai/stable-diffusion` | $0.003 | ⭐⭐⭐⭐ |
| `sdxl` | `blackboxai/stability-ai/sdxl` | $0.004 | ⭐⭐⭐⭐ |
| `sdxl-lightning-4step` | `blackboxai/bytedance/sdxl-lightning-4step` | $0.001 | ⭐⭐⭐ |

**Usage**:
```python
# توليد صورة
image_url = await llm.generate_image(
    prompt="A futuristic cityscape at sunset",
    model="flux-pro"  # اسم مختصر
)
print(f"Image URL: {image_url}")
```

**Example Output**:
```
Image URL: https://blackbox-cdn.com/images/abc123.png
```

---

### 🎥 Video Generation Models

| Model Short Name | Full Model ID | Cost | Duration | Quality |
|------------------|---------------|------|----------|---------|
| `veo-2` | `blackboxai/google/veo-2` | $0.50/sec | Up to 8s | ⭐⭐⭐⭐ |
| `veo-3` | `blackboxai/google/veo-3` | $0.75/sec | Up to 8s | ⭐⭐⭐⭐⭐ |
| `veo-3-fast` | `blackboxai/google/veo-3-fast` | $3.20/video | Up to 8s | ⭐⭐⭐⭐ |

**Usage**:
```python
# توليد فيديو
video_url = await llm.generate_video(
    prompt="A Tesla car driving on a highway at dusk",
    model="veo-2"
)
print(f"Video URL: {video_url}")
```

**Example Output**:
```
Video URL: https://blackbox-cdn.com/videos/xyz789.mp4
```

---

## 📖 Usage Examples

### 1. **Chat Completion**

```python
from app.infrastructure.external.llm.blackbox_llm import BlackboxLLM

llm = BlackboxLLM(
    api_key="sk-SuSCd8TN7baNnh2EcFnGzw",
    model="gpt-4o",
)

# Simple chat
response = await llm.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.content)  # "The capital of France is Paris."
print(response.usage)    # {"prompt_tokens": 20, "completion_tokens": 8, ...}
```

### 2. **Streaming Chat**

```python
# Streaming response
async for chunk in llm.stream_chat(
    messages=[
        {"role": "user", "content": "Tell me a story"}
    ]
):
    print(chunk.delta, end="", flush=True)
```

### 3. **Image Generation**

```python
# توليد صورة بجودة عالية
image_url = await llm.generate_image(
    prompt="A beautiful mountain landscape with a lake",
    model="flux-1.1-pro-ultra"
)

print(f"🎨 Generated: {image_url}")
```

#### Multiple Models Comparison

```python
prompts = [
    "A futuristic city",
    "A cute robot",
    "An abstract painting"
]

models = ["flux-pro", "stable-diffusion", "sdxl"]

for prompt in prompts:
    for model in models:
        image_url = await llm.generate_image(prompt, model=model)
        print(f"{model}: {image_url}")
```

### 4. **Video Generation**

```python
# توليد فيديو قصير
video_url = await llm.generate_video(
    prompt="A drone flying over a beautiful beach at sunset",
    model="veo-3"  # أعلى جودة
)

print(f"🎥 Video: {video_url}")
```

#### Batch Video Generation

```python
scenes = [
    "A car racing on a track",
    "A person walking in the rain",
    "A bird flying in slow motion"
]

for i, scene in enumerate(scenes):
    video_url = await llm.generate_video(scene, model="veo-2")
    print(f"Scene {i+1}: {video_url}")
```

### 5. **Web Search**

```python
# بحث على الإنترنت مع المصادر
result = await llm.web_search(
    query="What are the latest AI developments in 2025?"
)

print(result["content"])

print("\n📚 Sources:")
for source in result["sources"]:
    print(f"  - {source['title']}: {source['url']}")
```

**Example Output**:
```
Recent AI developments include GPT-5 release, improved multimodal models...

📚 Sources:
  - OpenAI News: https://openai.com/news
  - TechCrunch AI: https://techcrunch.com/ai
  - MIT Technology Review: https://technologyreview.com
```

### 6. **Using Factory**

```python
from app.infrastructure.external.llm.factory import get_llm_client

# إنشاء Blackbox client تلقائياً من Config
llm = get_llm_client(provider="blackbox", model="gpt-4o")

response = await llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# في .env
# =============================================================================
# LLM Provider Configuration
# =============================================================================
LLM_PROVIDER=blackbox  # deepseek, blackbox, openai

# Blackbox AI Configuration
BLACKBOX_API_KEY=sk-SuSCd8TN7baNnh2EcFnGzw
BLACKBOX_API_BASE=https://api.blackbox.ai

# Model Parameters
MODEL_NAME=gpt-4o
TEMPERATURE=0.7
MAX_TOKENS=2000
```

### Settings Class

```python
from app.core.config import get_settings

settings = get_settings()

print(settings.llm_provider)      # "blackbox"
print(settings.blackbox_api_key)  # "sk-..."
print(settings.model_name)        # "gpt-4o"
```

---

## 🧪 Testing

### Run Tests

```bash
# تشغيل اختبارات Blackbox
cd backend
pytest tests/unit/test_blackbox_llm.py -v

# تشغيل جميع الاختبارات
pytest tests/ -v
```

### Manual Test

```python
import asyncio
from app.infrastructure.external.llm.factory import test_llm_connection

# Test connection
async def main():
    success = await test_llm_connection(provider="blackbox")
    if success:
        print("✅ Blackbox connection successful!")
    else:
        print("❌ Blackbox connection failed!")

asyncio.run(main())
```

---

## 💰 Cost Estimates

### Chat Models

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o Mini | $0.15 | $0.60 |
| Claude 3.7 Sonnet | $3.00 | $15.00 |
| DeepSeek Chat | $0.14 | $0.28 |
| Gemini 2.0 Flash | $0.075 | $0.30 |

### Image Generation

| Model | Cost per Image | Estimated Usage |
|-------|---------------|----------------|
| Flux Pro | $0.055 | 18 images/$1 |
| Flux 1.1 Pro | $0.040 | 25 images/$1 |
| Flux Schnell | $0.003 | 333 images/$1 |
| Stable Diffusion | $0.003 | 333 images/$1 |
| SDXL | $0.004 | 250 images/$1 |

### Video Generation

| Model | Cost | Estimated Usage |
|-------|------|----------------|
| Veo 2 | $0.50/second | 2 seconds/$1 |
| Veo 3 | $0.75/second | 1.33 seconds/$1 |
| Veo 3 Fast | $3.20/video | ~0.3 videos/$1 |

**Monthly Budget Example (Moderate Usage)**:
```
Chat: 10M tokens/month         = $15-30
Images: 100 images/month       = $4-6
Videos: 20 videos/month        = $64
────────────────────────────────────
Total:                         ~$83-100/month
```

---

## 🎯 Best Practices

### 1. **Model Selection**

```python
# للمحادثات العامة - استخدم GPT-4o Mini (رخيص)
llm = BlackboxLLM(api_key=api_key, model="gpt-4o-mini")

# للمهام المعقدة - استخدم GPT-4o أو Claude
llm = BlackboxLLM(api_key=api_key, model="gpt-4o")

# للبحث - استخدم blackbox-search
llm = BlackboxLLM(api_key=api_key, model="blackbox-search")

# للصور عالية الجودة - استخدم Flux Pro
llm = BlackboxLLM(api_key=api_key, model="flux-1.1-pro-ultra")

# للصور السريعة - استخدم Flux Schnell
llm = BlackboxLLM(api_key=api_key, model="flux-schnell")
```

### 2. **Error Handling**

```python
from openai import APIError, RateLimitError

try:
    response = await llm.chat(messages=[...])
except RateLimitError:
    print("Rate limit exceeded - wait and retry")
except APIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 3. **Resource Management**

```python
# دائماً أغلق الـ client بعد الاستخدام
llm = BlackboxLLM(api_key=api_key)

try:
    response = await llm.chat(messages=[...])
finally:
    await llm.close()

# أو استخدم context manager (إذا كان مدعوماً)
async with BlackboxLLM(api_key=api_key) as llm:
    response = await llm.chat(messages=[...])
```

### 4. **Caching**

```python
# للاستعلامات المتكررة، استخدم cache
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_search(query: str):
    llm = BlackboxLLM(api_key=api_key, model="blackbox-search")
    result = await llm.web_search(query)
    await llm.close()
    return result
```

---

## 🔐 Security Best Practices

### 1. **API Key Management**

```bash
# ❌ Never hardcode API keys
api_key = "sk-SuSCd8TN7baNnh2EcFnGzw"  # Bad!

# ✅ Always use environment variables
api_key = os.getenv("BLACKBOX_API_KEY")  # Good!
```

### 2. **Input Validation**

```python
def validate_prompt(prompt: str) -> str:
    """Validate and sanitize user prompt."""
    if len(prompt) > 2000:
        raise ValueError("Prompt too long")
    
    # Remove sensitive patterns
    prompt = prompt.replace("API_KEY", "[REDACTED]")
    
    return prompt

# Use validated prompt
safe_prompt = validate_prompt(user_input)
response = await llm.chat(messages=[{"role": "user", "content": safe_prompt}])
```

### 3. **Rate Limiting**

```python
from asyncio import Semaphore

# Limit concurrent requests
semaphore = Semaphore(5)  # Max 5 concurrent requests

async def rate_limited_chat(messages):
    async with semaphore:
        return await llm.chat(messages)
```

---

## 📊 Monitoring & Logging

### 1. **Usage Tracking**

```python
import logging

logger = logging.getLogger(__name__)

async def tracked_chat(messages):
    start_time = time.time()
    
    try:
        response = await llm.chat(messages)
        
        # Log usage
        logger.info(
            f"Chat completed: "
            f"model={response.model}, "
            f"tokens={response.usage['total_tokens']}, "
            f"time={time.time() - start_time:.2f}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise
```

### 2. **Cost Tracking**

```python
class CostTracker:
    def __init__(self):
        self.total_cost = 0.0
        
    def track_chat(self, model, usage):
        # Simple cost calculation
        input_cost = usage["prompt_tokens"] / 1_000_000 * 2.5
        output_cost = usage["completion_tokens"] / 1_000_000 * 10.0
        cost = input_cost + output_cost
        
        self.total_cost += cost
        
        logger.info(f"Request cost: ${cost:.4f} | Total: ${self.total_cost:.2f}")
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. **Authentication Error**

```
Error: Invalid API key
```

**Solution**:
```bash
# تحقق من API Key
echo $BLACKBOX_API_KEY

# تأكد أنه يبدأ بـ sk-
# مثال: sk-SuSCd8TN7baNnh2EcFnGzw
```

#### 2. **Model Not Found**

```
Error: Model "xyz" not found
```

**Solution**:
```python
# استخدم الاسم المختصر الصحيح أو Full ID
model = "gpt-4o"  # ✅ Short name
# or
model = "blackboxai/openai/gpt-4o"  # ✅ Full ID
```

#### 3. **Rate Limit**

```
Error: Rate limit exceeded
```

**Solution**:
```python
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(5))
async def chat_with_retry(messages):
    return await llm.chat(messages)
```

---

## 📝 API Reference

### BlackboxLLM Class

```python
class BlackboxLLM:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    )
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs
    ) -> LLMResponse
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> AsyncIterator[StreamChunk]
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "flux-pro",
        **kwargs
    ) -> str
    
    async def generate_video(
        self,
        prompt: str,
        model: str = "veo-2",
        **kwargs
    ) -> str
    
    async def web_search(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Any]
    
    async def close()
```

---

## 🎉 Success Checklist

- [x] ✅ Blackbox LLM Client created
- [x] ✅ Chat models integrated (GPT-4, Claude, DeepSeek, etc.)
- [x] ✅ Image generation added (Flux, SDXL, Stable Diffusion)
- [x] ✅ Video generation added (Veo 2, Veo 3)
- [x] ✅ Web search integrated
- [x] ✅ Configuration updated
- [x] ✅ Tests created
- [x] ✅ Documentation complete

---

## 📞 Next Steps

### الآن يمكنك:

1. **تشغيل الاختبارات**:
   ```bash
   cd backend
   pytest tests/unit/test_blackbox_llm.py -v
   ```

2. **اختبار الـ API**:
   ```python
   from app.infrastructure.external.llm.factory import get_llm_client
   
   llm = get_llm_client(provider="blackbox", model="gpt-4o")
   response = await llm.chat(messages=[{"role": "user", "content": "Hello!"}])
   print(response.content)
   ```

3. **توليد صورة**:
   ```python
   image_url = await llm.generate_image("A beautiful sunset", model="flux-pro")
   print(image_url)
   ```

4. **توليد فيديو**:
   ```python
   video_url = await llm.generate_video("A car driving", model="veo-2")
   print(video_url)
   ```

---

**مبروك! 🎉 Blackbox AI جاهز للاستخدام!**

For questions or issues, refer to:
- Official Docs: https://docs.blackbox.ai/
- API Reference: https://api.blackbox.ai/docs
