# Cloud Run Jobs Sandbox - Browser/CDP Support Investigation

**Date:** 2025-12-28  
**Author:** Kilo Code  
**Status:** ✅ Investigation Complete - Solution Proposed

---

## Executive Summary

**Problem:** [`CloudRunJobsSandbox`](backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py:1143-1148) raises `NotImplementedError` when agents request browser functionality, blocking production deployment with Cloud Run Jobs.

**Root Cause:** Browser automation requires persistent Chrome DevTools Protocol (CDP) server, which is incompatible with ephemeral Cloud Run Jobs architecture.

**Impact:** **CRITICAL** - ALL agents require browser access. 100% of agent tasks will fail with CloudRunJobsSandbox.

**Recommended Solution:** **Option D (Optional Browser) + Option E (Hybrid Approach)** - Implement graceful degradation with intelligent sandbox selection.

---

## Investigation Findings

### 1. Browser/CDP Usage Analysis

#### Architecture
- **DockerSandbox** runs persistent container with:
  - Chrome browser with CDP enabled on port 9222
  - VNC server on port 5901 
  - HTTP API on port 8080
- **PlaywrightBrowser** connects via `playwright.chromium.connect_over_cdp(cdp_url)`
- **CDP Health Check** validates browser readiness before task execution

#### Integration Points

**Critical Path:**
```python
# backend/app/domain/services/agent_domain_service.py:68-71
browser = await sandbox.get_browser()
if not browser:
    logger.error(f"Failed to get browser for Sandbox {sandbox_id}")
    raise RuntimeError(f"Failed to get browser for Sandbox {sandbox_id}")
```

**Agent Initialization:**
```python
# backend/app/domain/services/flows/plan_act.py:56-72
def __init__(self, ..., sandbox: Sandbox, browser: Browser, ...):
    tools = [
        ShellTool(sandbox),
        BrowserTool(browser),  # ← ALWAYS included
        FileTool(sandbox),
        MessageTool(),
        WebDevTool(sandbox),
    ]
```

### 2. Tools Requiring Browser

**[`BrowserTool`](backend/app/domain/services/tools/browser.py)** provides 14 browser automation methods:

| Method | Description | Usage |
|--------|-------------|-------|
| `browser_view` | View current page content | High frequency |
| `browser_navigate` | Navigate to URL | High frequency |
| `browser_click` | Click elements | High frequency |
| `browser_input` | Fill form fields | High frequency |
| `browser_scroll_down/up` | Scroll page | Medium frequency |
| `browser_console_exec` | Execute JavaScript | Medium frequency |
| `browser_restart` | Restart browser | Low frequency |
| `browser_move_mouse` | Move cursor | Low frequency |
| `browser_press_key` | Simulate keypress | Medium frequency |
| `browser_select_option` | Select dropdown | Medium frequency |
| `browser_console_view` | View console logs | Low frequency |
| `browser_smart_scroll` | Infinite scroll handling | Medium frequency |
| `browser_navigate_robust` | Navigation with retry | Medium frequency |

**Usage Patterns from System Prompts:**
```python
# backend/app/domain/services/prompts/system.py:48-58
<browser_rules>
- Must use browser tools to access and comprehend all URLs provided by users
- Must use browser tools to access URLs from search tool results
- Actively explore valuable links for deeper information
- Browser tools only return elements in visible viewport by default
- Browser tools automatically attempt to extract page content
</browser_rules>
```

**Key Insight:** Browser is **MANDATORY** for web research, content access, and verification tasks - which represent the majority of agent use cases.

### 3. Agents Requiring Browser

**ALL agents require browser** because:
1. [`PlanActFlow`](backend/app/domain/services/flows/plan_act.py:56-72) always creates `BrowserTool`
2. [`ExecutionAgent`](backend/app/domain/services/agents/execution.py) receives browser tools
3. Agent system prompts mandate browser use for web content access
4. Search tool results require browser for URL access

**Agent Creation Flow:**
```
agent_domain_service._create_task()
  ↓
sandbox.get_browser() [REQUIRED - raises if fails]
  ↓
AgentTaskRunner(browser=browser)
  ↓
PlanActFlow(browser=browser)
  ↓
Tools include BrowserTool(browser)
```

### 4. Current CloudRunJobsSandbox Limitation

**[`cloudrun_jobs_sandbox.py:1143-1148`](backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py:1143-1148)**:
```python
async def get_browser(self) -> Browser:
    """Get browser instance - Not supported in Cloud Run Jobs"""
    raise NotImplementedError(
        "Browser/CDP not available in Cloud Run Jobs sandbox. "
        "CDP requires persistent container with Chrome DevTools Protocol port."
    )
```

**Why CDP Cannot Work with Cloud Run Jobs:**
- ❌ **Jobs are ephemeral** - Container dies after execution
- ❌ **No network persistence** - Cannot maintain CDP connection
- ❌ **No state retention** - Browser state lost between commands  
- ❌ **Startup overhead** - Chrome initialization too slow for per-command execution
- ❌ **Resource constraints** - Jobs have memory/CPU limits unsuitable for Chrome

---

## Solution Options

### Option A: Separate Browser Service ⭐ **RECOMMENDED FOR PRODUCTION**

**Architecture:**
```
┌─────────────────────────────┐
│  Cloud Run Service          │
│  (Long-running)             │
│                             │
│  ┌──────────────────────┐  │
│  │ Chrome + CDP:9222    │  │
│  │ VNC:5901             │  │
│  │ API:8080             │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
            ↑
            │ connect_over_cdp()
            │
┌─────────────────────────────┐
│  Cloud Run Jobs             │
│  (Executor Container)       │
│                             │
│  CloudRunJobsSandbox        │
│  + PlaywrightBrowser        │
└─────────────────────────────┘
```

**Implementation:**
1. Deploy Chrome container as Cloud Run Service (always-on)
2. Configure CloudRunJobsSandbox with browser service URL
3. Implement `get_browser()` to return `PlaywrightBrowser(service_cdp_url)`

**Pros:**
- ✅ Full CDP/browser support
- ✅ Clean separation of concerns
- ✅ Matches DockerSandbox architecture
- ✅ Scalable (multiple executor jobs can share browser service)
- ✅ Browser state persists across job executions

**Cons:**
- ❌ Additional service to deploy and manage
- ❌ Increased cost (always-running service)
- ❌ Network latency between Jobs and Service
- ❌ Need session management for multi-user scenarios

**Cost Estimate:** ~$15-30/month for always-on Cloud Run Service (1 instance, min CPU)

---

### Option B: Headless Chrome in Executor Container

**Architecture:**
```
┌─────────────────────────────┐
│  Cloud Run Jobs             │
│  (Executor Container)       │
│                             │
│  ┌──────────────────────┐  │
│  │ Chrome + CDP:9222    │  │
│  │ (started per job)    │  │
│  └──────────────────────┘  │
│                             │
│  CloudRunJobsSandbox        │
│  + PlaywrightBrowser        │
└─────────────────────────────┘
```

**Implementation:**
1. Add Chrome to executor container image
2. Start Chrome in executor entrypoint
3. Connect to local CDP (localhost:9222)

**Pros:**
- ✅ Self-contained solution
- ✅ No additional services
- ✅ Simple deployment

**Cons:**
- ❌ Slow startup (Chrome initialization adds 3-5s per job)
- ❌ High memory usage (Chrome needs 200-300MB)
- ❌ Browser state lost between jobs
- ❌ Inefficient resource usage
- ❌ Cloud Run Jobs may timeout during Chrome startup

**Not Recommended:** Incompatible with Cloud Run Jobs constraints

---

### Option C: CDP Emulation/Proxy

**Architecture:**
```
┌─────────────────────────────┐
│  Cloud Run Jobs             │
│                             │
│  CDP Emulation Layer        │
│    ↓ translates to          │
│  Puppeteer/Selenium Grid    │
└─────────────────────────────┘
```

**Implementation:**
1. Create CDP protocol emulator
2. Translate CDP commands to alternative automation
3. Implement subset of CDP spec

**Pros:**
- ✅ No persistent Chrome needed
- ✅ Could use managed browser services

**Cons:**
- ❌ Extremely complex (CDP has 100+ domains)
- ❌ Incomplete protocol support
- ❌ Maintenance burden
- ❌ Playwright tightly coupled to real CDP

**Not Recommended:** Engineering complexity far exceeds benefit

---

### Option D: Optional Browser (Make Tools Gracefully Degrade) ⭐ **RECOMMENDED SHORT-TERM**

**Architecture:**
```python
# Modify agent initialization
if sandbox_supports_browser:
    browser = await sandbox.get_browser()
    tools.append(BrowserTool(browser))
else:
    # Skip browser tools, use alternatives
    tools.append(SearchTool(search_engine))  # Already present
```

**Implementation:**
1. Add `supports_browser()` method to Sandbox protocol
2. Modify agent flow to conditionally include BrowserTool
3. Update system prompts to adapt when browser unavailable
4. Enhance SearchTool to provide rich content extraction

**Pros:**
- ✅ CloudRunJobsSandbox works for CLI-only tasks
- ✅ Minimal code changes
- ✅ Quick to implement (1-2 days)
- ✅ Backward compatible

**Cons:**
- ❌ Reduced functionality for web tasks
- ❌ Agents cannot access web content directly
- ❌ User experience degradation
- ❌ Search results less useful without browser verification

**Use Cases That Work:**
- Pure coding tasks (write/edit files)
- System administration
- Data processing
- File manipulation
- CLI tool usage

**Use Cases That Fail:**
- Web research
- URL content extraction
- Form automation
- Visual verification
- Dynamic web scraping

---

### Option E: Hybrid Approach (Smart Sandbox Selection) ⭐ **RECOMMENDED PRODUCTION**

**Architecture:**
```python
# Intelligent sandbox selection based on task requirements
class SandboxSelector:
    async def select_sandbox(self, message: Message) -> Sandbox:
        if self.requires_browser(message):
            return await DockerSandbox.create()  # Full browser support
        else:
            return await CloudRunJobsSandbox.create()  # Cost-effective
    
    def requires_browser(self, message: Message) -> bool:
        # Analyze message for web-related keywords
        web_indicators = ['url', 'website', 'browse', 'search', 'web', 'http']
        return any(indicator in message.message.lower() for indicator in web_indicators)
```

**Implementation:**
1. Implement `SandboxSelector` with task analysis
2. Default to CloudRunJobsSandbox for cost efficiency
3. Fallback to DockerSandbox when browser detected
4. Add user preference override

**Pros:**
- ✅ Best of both worlds
- ✅ Cost-effective for CLI tasks
- ✅ Full functionality when needed
- ✅ Transparent to users
- ✅ Gradual migration path

**Cons:**
- ❌ Need task classification logic
- ❌ Potential misclassification
- ❌ Maintains both implementations

---

## Recommended Implementation Plan

### Phase 1: Short-Term (Optional Browser) - **1-2 Days**

**Goal:** Make CloudRunJobsSandbox functional for non-browser tasks

**Tasks:**
1. Add `supports_browser() -> bool` to Sandbox protocol
2. Modify `agent_domain_service.py` to handle browser unavailability
3. Update `PlanActFlow` to conditionally include BrowserTool
4. Update system prompts with browser availability context
5. Add graceful error handling for browser-requiring tasks

**Code Changes:**
```python
# backend/app/domain/external/sandbox.py
class Sandbox(Protocol):
    def supports_browser(self) -> bool:
        """Whether this sandbox supports browser automation"""
        return True  # Default for DockerSandbox
    
# backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py
def supports_browser(self) -> bool:
    return False

# backend/app/domain/services/agent_domain_service.py
async def _create_task(self, session: Session) -> Task:
    sandbox = await self._sandbox_cls.create()
    
    # Optional browser
    browser = None
    if sandbox.supports_browser():
        browser = await sandbox.get_browser()
    
    task_runner = AgentTaskRunner(
        sandbox=sandbox,
        browser=browser,  # May be None
        # ...
    )
```

**Testing:**
- ✅ CLI tasks work with CloudRunJobsSandbox
- ✅ Web tasks gracefully fail with helpful message
- ✅ DockerSandbox unchanged

---

### Phase 2: Production (Browser Service) - **1 Week**

**Goal:** Full browser support for CloudRunJobsSandbox via dedicated service

**Tasks:**
1. Create browser service container (Chrome + CDP + API)
2. Deploy as Cloud Run Service with session management
3. Implement connection pooling and health checks
4. Add `CloudRunBrowserService` class
5. Integrate with CloudRunJobsSandbox
6. Add monitoring and auto-scaling

**Architecture:**
```
┌──────────────────────────────────────┐
│  Browser Service (Cloud Run Service) │
│                                       │
│  ┌────────────────────────────────┐  │
│  │ Session Manager                │  │
│  │  - Allocate CDP ports          │  │
│  │  - Track sessions              │  │
│  │  - Cleanup idle browsers       │  │
│  └────────────────────────────────┘  │
│                                       │
│  ┌────────────────────────────────┐  │
│  │ Chrome Instances Pool          │  │
│  │  - Instance 1: CDP:9222        │  │
│  │  - Instance 2: CDP:9223        │  │
│  │  - Instance N: CDP:922N        │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

**Cost Optimization:**
- Use min-instances=1 (always-on for fast response)
- Implement session timeout (cleanup idle browsers)
- Share browser instances across users when possible
- Consider regional deployment for latency

**Estimated Cost:** $20-40/month for production load

---

### Phase 3: Optimization (Hybrid Approach) - **3-5 Days**

**Goal:** Intelligent sandbox selection for cost optimization

**Tasks:**
1. Implement `SandboxSelector` with task classification
2. Add ML-based task analysis (optional)
3. User preference settings
4. Performance monitoring
5. A/B testing framework

**Classification Rules:**
```python
HIGH_PRIORITY_BROWSER = [
    "browse", "website", "url", "http", "search web",
    "scrape", "visit", "navigate", "screenshot"
]

LOW_PRIORITY_BROWSER = [
    "search" (alone), "find", "look up"  # Can use search API
]

NO_BROWSER_NEEDED = [
    "create file", "write code", "analyze", "calculate",
    "convert", "format", "process", "fix bug"
]
```

---

## Implementation Complexity & Timeline

| Phase | Complexity | Timeline | Risk |
|-------|-----------|----------|------|
| Phase 1: Optional Browser | Low | 1-2 days | Low |
| Phase 2: Browser Service | Medium | 1 week | Medium |
| Phase 3: Hybrid Selection | Medium | 3-5 days | Low |

**Total Timeline:** 2-3 weeks for complete solution

---

## Decision Matrix

| Criteria | Option A (Service) | Option D (Optional) | Option E (Hybrid) |
|----------|-------------------|---------------------|-------------------|
| Implementation Time | Medium (1 week) | Fast (1-2 days) | Medium (2 weeks) |
| Functionality | Full ⭐ | Limited | Full ⭐ |
| Cost | Medium ($20-40/mo) | Low ⭐ | Low-Medium ⭐ |
| Complexity | Medium | Low ⭐ | Medium |
| Production Ready | Yes ⭐ | Partial | Yes ⭐ |
| User Experience | Excellent ⭐ | Degraded | Excellent ⭐ |

---

## Recommended Action Plan

### Immediate (This Week):
1. **Implement Phase 1 (Optional Browser)** to unblock CloudRunJobsSandbox
2. Deploy with feature flag: `USE_CLOUDRUN_JOBS_SANDBOX=false` (safe default)
3. Document browser limitations for users

### Short-Term (Next 2 Weeks):
4. **Implement Phase 2 (Browser Service)** for production
5. Deploy browser service to staging environment
6. Performance and cost testing

### Medium-Term (Next Month):
7. **Implement Phase 3 (Hybrid)** for optimization
8. Enable CloudRunJobsSandbox with intelligent selection
9. Monitor cost savings vs DockerSandbox

---

## Success Metrics

- ✅ **Functionality:** 100% of browser tasks work with browser service
- ✅ **Performance:** <2s browser connection time
- ✅ **Reliability:** 99.9% browser service uptime
- ✅ **Cost:** <$50/month for browser infrastructure
- ✅ **User Experience:** No degradation vs DockerSandbox

---

## Conclusion

**Browser/CDP support is CRITICAL** - without it, CloudRunJobsSandbox cannot replace DockerSandbox in production. The recommended approach is a **three-phase implementation**:

1. **Phase 1 (Immediate):** Optional browser support for basic functionality
2. **Phase 2 (Production):** Dedicated browser service for full capabilities  
3. **Phase 3 (Optimization):** Intelligent hybrid selection for cost efficiency

This approach provides:
- ✅ Rapid unblocking of CloudRunJobsSandbox development
- ✅ Full production capabilities within 2-3 weeks
- ✅ Cost-effective operation (<$50/month additional)
- ✅ Excellent user experience
- ✅ Clear migration path from DockerSandbox

**Next Steps:**
1. Review and approve this investigation report
2. Prioritize Phase 1 implementation (1-2 days)
3. Plan Phase 2 browser service architecture
4. Allocate resources for 2-3 week implementation

---

**Investigation Complete** ✅  
**Solution Viable** ✅  
**Ready for Implementation** ✅