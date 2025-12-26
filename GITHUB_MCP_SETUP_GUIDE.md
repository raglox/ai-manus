# 🚀 GitHub MCP Integration - Production Setup Guide

**Date**: 2025-12-26  
**Status**: Ready for Production Testing  
**Goal**: Enable autonomous GitHub operations via MCP

---

## 📋 Overview

This guide explains how to enable the AI-Manus agent to perform real GitHub operations autonomously using the Model Context Protocol (MCP).

### What This Enables

The agent can now:
- ✅ Create and manage repositories
- ✅ Read file contents
- ✅ Create and update issues
- ✅ Create pull requests
- ✅ Search code and repositories
- ✅ Manage branches and commits

**All without hardcoded GitHub API calls!**

---

## 🔧 Setup Instructions

### Step 1: Get GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a descriptive name: `MCP Integration Token`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `write:packages` (Upload packages)
   - ✅ `read:org` (Read org data)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### Step 2: Configure Environment

**Option A: Environment Variable (Recommended)**

```bash
# Add to your .env file
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Or export in shell
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

**Option B: Docker Environment**

```yaml
# In docker-compose.yml
services:
  backend:
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
```

### Step 3: Verify Configuration

```bash
# Check that token is set
echo $GITHUB_TOKEN

# Should output: ghp_xxxxxxxxxxxxxxxxxxxx
```

### Step 4: Update mcp_config.json (Already Done ✅)

The configuration is already updated:

```json
{
  "mcpServers": {
    "github": {
      "description": "GitHub operations (repos, issues, PRs, files)",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

---

## 🧪 Testing

### Quick Test (Manual)

```python
from app.domain.services.mcp_manager import McpConnectionManager
from app.infrastructure.external.sandbox.docker_sandbox import StatefulDockerSandbox
import asyncio
import os

async def test_github_mcp():
    # Ensure token is set
    os.environ['GITHUB_TOKEN'] = 'ghp_your_token_here'
    
    # Create sandbox
    sandbox = StatefulDockerSandbox()
    await sandbox.initialize()
    
    # Create MCP manager
    manager = McpConnectionManager(
        sandbox=sandbox,
        session_id="test-session",
        config_path="mcp_config.json"
    )
    
    # Initialize
    success = await manager.initialize()
    print(f"Initialized: {success}")
    
    # Get tools
    tools = manager.get_available_tools()
    github_tools = [t for t in tools if t.server_name == 'github']
    print(f"GitHub tools: {len(github_tools)}")
    for tool in github_tools[:5]:
        print(f"  - {tool.name}: {tool.description}")
    
    # Cleanup
    await manager.shutdown()
    await sandbox.destroy()

# Run
asyncio.run(test_github_mcp())
```

### Full Integration Test

```bash
# Set GitHub token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Run test suite
cd backend
pytest tests/integration/test_github_flow.py -v -s

# Expected output:
# test_github_server_connection ... PASSED
# test_github_tools_discovery ... PASSED
# test_github_create_issue ... PASSED
# test_full_github_workflow ... PASSED
```

---

## 📊 Available GitHub Tools

The MCP GitHub server provides these tools (auto-discovered):

### Repository Operations
- `create_repository` - Create a new repository
- `get_repository` - Get repository details
- `list_repositories` - List user repositories
- `fork_repository` - Fork a repository

### File Operations
- `get_file_contents` - Read file from repo
- `push_files` - Push files to repo
- `create_or_update_file` - Create/update single file
- `search_code` - Search code across repos

### Issue Operations
- `create_issue` - Create a new issue
- `update_issue` - Update existing issue
- `list_issues` - List repository issues
- `get_issue` - Get issue details

### Pull Request Operations
- `create_pull_request` - Create a PR
- `list_pull_requests` - List PRs
- `get_pull_request` - Get PR details
- `merge_pull_request` - Merge a PR

### Branch Operations
- `create_branch` - Create a branch
- `list_branches` - List branches
- `get_branch` - Get branch details

---

## 🎯 Usage with Agent

### Enable MCP Sandbox Mode

```python
# In your agent initialization
flow = PlanActFlow(
    agent_id="agent-123",
    session_id="session-456",
    sandbox=sandbox,
    mcp_tool=mcp_tool,
    use_mcp_sandbox=True,  # ✅ Enable MCP Sandbox
    ...
)
```

### Example Agent Prompts

**Create an Issue:**
```
Create a GitHub issue in raglox/ai-manus titled "Add user authentication" 
with description "Implement JWT-based authentication for API endpoints"
```

**Read Code:**
```
Read the contents of app/main.py from raglox/ai-manus repository
```

**Create PR:**
```
Create a pull request in raglox/ai-manus from feature/auth to main 
with title "Add authentication" and description "Implements JWT auth"
```

The agent will:
1. Discover available GitHub tools
2. Select the appropriate tool (e.g., `create_issue`)
3. Extract required parameters from your prompt
4. Execute the tool via MCP
5. Return the result

---

## 🔍 Troubleshooting

### Issue: "GitHub token not found"

**Solution:**
```bash
# Verify token is set
echo $GITHUB_TOKEN

# If empty, set it
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Verify it's passed to Docker
docker exec <container> env | grep GITHUB_TOKEN
```

### Issue: "Failed to connect to GitHub server"

**Solution:**
1. Check Node.js is installed:
   ```bash
   node --version  # Should be v22.x
   npx --version
   ```

2. Test GitHub server manually:
   ```bash
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx npx -y @modelcontextprotocol/server-github
   ```

3. Check sandbox environment:
   ```python
   # Ensure token is passed to sandbox
   os.environ['GITHUB_TOKEN'] = 'ghp_xxx'
   ```

### Issue: "Tool not found"

**Solution:**
- Tools are discovered at runtime
- Check server initialization:
  ```python
  status = manager.get_status()
  print(status['tools_by_server'])
  ```
- Look for exact tool name:
  ```python
  tools = manager.get_available_tools()
  for tool in tools:
      if 'create' in tool.name and 'issue' in tool.name:
          print(tool.name)
  ```

### Issue: "403 Forbidden"

**Solution:**
- Token lacks required permissions
- Regenerate token with correct scopes
- Verify token is valid:
  ```bash
  curl -H "Authorization: token ghp_xxx" https://api.github.com/user
  ```

---

## 📈 Performance Notes

### Cold Start
- First connection: ~5-10 seconds (downloading MCP server)
- Subsequent connections: ~2-3 seconds

### Tool Execution
- Simple operations (get file): ~1-2 seconds
- Complex operations (create PR): ~3-5 seconds

### Caching
- MCP servers are cached in Docker container
- Tool schemas are cached in memory
- No re-download on subsequent runs

---

## 🔒 Security Considerations

### Token Security
- ✅ Token passed via environment variable
- ✅ Never hardcoded in config files
- ✅ Not logged or exposed in responses
- ✅ Runs in isolated Docker sandbox

### Sandbox Isolation
- MCP server runs inside Docker
- No access to host system
- Limited to repository permissions
- Can be killed/reset at any time

### Token Permissions
- Use fine-grained tokens when possible
- Limit scope to necessary permissions
- Rotate tokens regularly
- Monitor token usage

---

## 📝 Example Scenarios

### Scenario 1: Create Release Notes

**Agent Prompt:**
```
Read the last 10 commits from raglox/ai-manus and create an issue 
with a summary of changes as release notes for v2.0
```

**Agent Actions:**
1. Uses `list_commits` to get recent commits
2. Processes commit messages
3. Uses `create_issue` to create release notes issue

### Scenario 2: Code Review Assistant

**Agent Prompt:**
```
Get the contents of app/api/routes.py and create an issue listing 
any potential security concerns
```

**Agent Actions:**
1. Uses `get_file_contents` to read file
2. Analyzes code for security issues
3. Uses `create_issue` to document findings

### Scenario 3: Automated PR

**Agent Prompt:**
```
Create a branch called feature/add-logging, add a logging.py file with 
basic logging setup, commit it, and create a PR
```

**Agent Actions:**
1. Uses `create_branch` to create feature branch
2. Uses `push_files` to add logging.py
3. Uses `create_pull_request` to open PR

---

## ✅ Verification Checklist

Before going to production:

- [ ] GitHub token generated with correct scopes
- [ ] Token set in environment variable
- [ ] mcp_config.json includes GitHub server
- [ ] Node.js available in Docker (v22+)
- [ ] Integration tests passing
- [ ] Token permissions verified
- [ ] Agent can discover GitHub tools
- [ ] At least one successful GitHub operation

---

## 🎉 Success Criteria

Your setup is working if:

1. ✅ `manager.get_status()` shows GitHub server connected
2. ✅ GitHub tools appear in `manager.get_available_tools()`
3. ✅ Agent can execute at least one GitHub operation
4. ✅ Operations appear in GitHub (issues, commits, etc.)

---

## 📞 Support

### Documentation
- MCP Spec: https://modelcontextprotocol.io/
- GitHub Server: https://github.com/modelcontextprotocol/servers
- Our Docs: `MCP_INTEGRATION_COMPLETE.md`

### Testing
- Unit Tests: `tests/unit/test_mcp_integration.py`
- Integration Tests: `tests/integration/test_github_flow.py`
- Agent Tests: `tests/integration/test_agent_mcp_integration.py`

---

**Setup Guide Version**: 1.0  
**Last Updated**: 2025-12-26  
**Status**: Production Ready ✅
