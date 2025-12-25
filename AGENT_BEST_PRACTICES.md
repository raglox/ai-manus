# Agent Best Practices - Stateful Sandbox Usage Guide

## 🎯 Overview

This guide provides best practices for AI agents using the Stateful Sandbox. The sandbox maintains persistent context (ENV, CWD) between commands and supports background processes.

---

## 📚 Core Concepts

### 1. Stateful Sessions

**What are Sessions?**
- Sessions maintain ENV variables and CWD between commands
- Each session has a unique ID (default: `"default"`)
- Sessions are isolated from each other

**Why Use Sessions?**
- ✅ No need to re-export ENV vars
- ✅ Navigate directories once, stay there
- ✅ Cleaner command sequences
- ✅ Better debugging (session state visible)

### 2. Background Processes

**When to Use Background?**
- Web servers (e.g., `npm run dev`, `python -m http.server`)
- Database servers
- Long-running processes
- File watchers

**How to Use:**
- Append `&` to command: `npm run dev &`
- Returns immediately with PID
- Process runs until killed or container stops

---

## 🚀 Agent Prompt Guidelines

### Recommended System Prompt Addition

```
You are an AI assistant with access to a Stateful Sandbox environment. The sandbox maintains:

1. **Persistent ENV Variables**: Any variable you export stays active for the session
   - Example: `export API_KEY=abc123` persists across commands
   
2. **Persistent Working Directory**: Directory changes persist
   - Example: After `cd /project`, you stay in /project
   
3. **Background Processes**: Commands ending with & run in background
   - Example: `npm run dev &` starts server without blocking

**Best Practices:**
- Set up ENV vars once at the start
- Navigate to project root early
- Use background processes for servers
- Check background logs if processes fail
- Clean up sessions when done

**Session Management:**
- Default session: Used automatically
- Create new session: Use `shell_exec(command="...", id="my_session")`
- List sessions: Use session management API
- Close session: Cleanup when done

**Background Process Management:**
- Start: `command &`
- List: Check background_pids in result
- Kill: Use kill_background_process API
- Logs: Use get_background_logs(pid)
```

---

## 📖 Usage Patterns by Task

### Pattern 1: Python Project Setup

**Inefficient (Old Way):**
```python
# Every command needs full context
shell_exec("cd /project && export PYTHONPATH=/project && python main.py")
shell_exec("cd /project && export PYTHONPATH=/project && python test.py")
shell_exec("cd /project && export PYTHONPATH=/project && python build.py")
```

**Efficient (New Way):**
```python
# Set up once
shell_exec("cd /project")
shell_exec("export PYTHONPATH=/project")

# Now just use commands
shell_exec("python main.py")
shell_exec("python test.py")
shell_exec("python build.py")
```

---

### Pattern 2: Web Development Workflow

**Task:** Start dev server, make changes, test

```python
# 1. Navigate and set up
shell_exec("cd /project/frontend")
shell_exec("export NODE_ENV=development")

# 2. Install dependencies (if needed)
shell_exec("npm install")

# 3. Start dev server in background
result = shell_exec("npm run dev &")
dev_server_pid = result.data["background_pid"]

# 4. Wait for server to start
import asyncio
await asyncio.sleep(3)

# 5. Make changes using file_editor
file_tool.file_str_replace(
    path="/project/frontend/src/App.js",
    old_str="Hello",
    new_str="Hello World"
)

# 6. Test the server
test_result = shell_exec("curl http://localhost:3000")

# 7. Cleanup when done
kill_background_process(pid=dev_server_pid)
```

---

### Pattern 3: Multi-Service Architecture

**Task:** Run backend + frontend + database

```python
# Start database in session1
shell_exec("redis-server &", id="db_session")

# Start backend in session2
shell_exec("cd /project/backend", id="backend_session")
shell_exec("export DB_URL=redis://localhost:6379", id="backend_session")
backend_result = shell_exec("python app.py &", id="backend_session")

# Start frontend in session3
shell_exec("cd /project/frontend", id="frontend_session")
shell_exec("export API_URL=http://localhost:8000", id="frontend_session")
frontend_result = shell_exec("npm run dev &", id="frontend_session")

# Each service isolated in its own session
# Easy to manage and debug separately
```

---

### Pattern 4: File Editing with Context

**Task:** Refactor code across multiple files

```python
# Navigate to project
shell_exec("cd /project/src")

# File operations maintain context
file_tool.file_view(path="utils.py")  # Relative to /project/src
file_tool.file_str_replace(
    path="utils.py",
    old_str="old_function",
    new_str="new_function"
)

file_tool.file_view(path="main.py")
file_tool.file_str_replace(
    path="main.py",
    old_str="old_function",
    new_str="new_function"
)

# Verify changes
shell_exec("grep -r 'new_function' .")
```

---

### Pattern 5: Testing Workflow

**Task:** Run tests with proper environment

```python
# Set up test environment
shell_exec("cd /project")
shell_exec("export TESTING=true")
shell_exec("export DB_URL=sqlite:///:memory:")

# Run different test suites
shell_exec("pytest tests/unit/")
shell_exec("pytest tests/integration/")
shell_exec("pytest tests/e2e/")

# ENV persists, no need to re-export
```

---

## ⚠️ Common Pitfalls & Solutions

### Pitfall 1: Forgetting Background Processes

**Problem:**
```python
shell_exec("npm run dev &")  # Starts server
# ... do other work ...
# Server still running! Wasting resources
```

**Solution:**
```python
result = shell_exec("npm run dev &")
pid = result.data["background_pid"]

# ... do your work ...

# Always cleanup
kill_background_process(pid=pid)
```

---

### Pitfall 2: Session Confusion

**Problem:**
```python
shell_exec("export VAR=value1")  # default session
shell_exec("echo $VAR", id="other_session")  # Empty! Different session
```

**Solution:**
```python
# Stick to one session or be explicit
session_id = "my_work"
shell_exec("export VAR=value1", id=session_id)
shell_exec("echo $VAR", id=session_id)  # Works!
```

---

### Pitfall 3: Not Checking Background Process Status

**Problem:**
```python
shell_exec("npm run dev &")
# Assume it's running
shell_exec("curl http://localhost:3000")  # Fails if server crashed
```

**Solution:**
```python
result = shell_exec("npm run dev &")
pid = result.data["background_pid"]

# Wait and check
await asyncio.sleep(2)
is_running = await sandbox._check_pid_running(pid)

if not is_running:
    logs = await sandbox.get_background_logs(pid)
    print(f"Server failed to start. Logs: {logs}")
```

---

### Pitfall 4: Path Confusion

**Problem:**
```python
shell_exec("cd /project")
file_tool.file_view(path="main.py")  # Where is this relative to?
```

**Solution:**
```python
# Always use absolute paths for file operations
shell_exec("cd /project")
pwd_result = shell_exec("pwd")
cwd = pwd_result.data["cwd"]  # "/project"

file_tool.file_view(path=f"{cwd}/main.py")  # Explicit
```

---

## 🔍 Debugging Tips

### Tip 1: Check Session State

```python
# List all sessions
sessions = sandbox.list_sessions()
for session in sessions:
    print(f"Session: {session['session_id']}")
    print(f"  CWD: {session['cwd']}")
    print(f"  ENV: {session['env_vars']}")
    print(f"  Background: {session['background_pids']}")
```

### Tip 2: Monitor Background Processes

```python
# List all background processes
processes = await sandbox.list_background_processes()
for proc in processes:
    if not proc['running']:
        print(f"⚠️  Dead process: PID {proc['pid']} - {proc['command']}")
        logs = await sandbox.get_background_logs(proc['pid'])
        print(f"   Logs: {logs}")
```

### Tip 3: Session Cleanup

```python
# Before starting complex task
sandbox.cleanup_all_sessions(exclude=["default"])

# Clean start for your work
shell_exec("cd /project")
```

---

## 🎯 Advanced Patterns

### Pattern: Long-Running Task with Progress

```python
# Start task in background
result = shell_exec("./long_running_script.sh > /tmp/progress.log 2>&1 &")
pid = result.data["background_pid"]

# Poll progress
for i in range(10):
    await asyncio.sleep(5)
    
    # Check if still running
    is_running = await sandbox._check_pid_running(pid)
    if not is_running:
        print("Task completed!")
        break
    
    # Show progress
    logs = await sandbox.get_background_logs(pid)
    print(f"Progress: {logs[-200:]}")  # Last 200 chars
```

### Pattern: Graceful Shutdown

```python
try:
    # Start services
    result1 = shell_exec("service1 &")
    result2 = shell_exec("service2 &")
    
    # Do work
    # ...
    
finally:
    # Always cleanup
    await sandbox.kill_background_process(session_id="default")
    sandbox.close_session("default")
```

### Pattern: Session Isolation for Security

```python
# Untrusted code? Use isolated session
untrusted_session = "sandbox_untrusted"
shell_exec("cd /tmp", id=untrusted_session)
shell_exec("export PATH=/usr/bin:/bin", id=untrusted_session)  # Limited PATH

# Run untrusted code
result = shell_exec("./untrusted_script.sh", id=untrusted_session)

# Cleanup immediately
sandbox.close_session(untrusted_session)
```

---

## 📊 Performance Guidelines

### DO:
- ✅ Reuse sessions for related tasks
- ✅ Set ENV vars once per session
- ✅ Use background for long tasks
- ✅ Clean up sessions when done

### DON'T:
- ❌ Create too many sessions (100+)
- ❌ Export same var repeatedly
- ❌ Keep unused background processes
- ❌ Mix unrelated work in one session

---

## 🔒 Security Best Practices

### 1. Sensitive Data

```python
# Good: Use ENV for secrets
shell_exec("export API_KEY=$(cat /secure/key.txt)")
shell_exec("curl -H 'Authorization: Bearer $API_KEY' ...")

# Bad: Hardcode secrets
shell_exec("curl -H 'Authorization: Bearer abc123' ...")  # Visible in logs!
```

### 2. Session Isolation

```python
# Good: Separate sessions for different security contexts
shell_exec("export ADMIN_TOKEN=...", id="admin_session")
shell_exec("export USER_TOKEN=...", id="user_session")

# Bad: Mix in same session
shell_exec("export ADMIN_TOKEN=...")
shell_exec("export USER_TOKEN=...")  # Both accessible!
```

### 3. Cleanup

```python
# Good: Always cleanup sensitive sessions
try:
    shell_exec("export SECRET=...", id="temp")
    # ... work ...
finally:
    sandbox.close_session("temp")  # Destroys ENV

# Bad: Leave sensitive data
shell_exec("export SECRET=...")  # Persists forever!
```

---

## 📝 Summary

**Key Takeaways:**
1. Sessions maintain ENV + CWD automatically
2. Use `&` for background processes
3. Always cleanup background processes and sessions
4. Check logs when processes fail
5. Isolate unrelated work in separate sessions
6. Use absolute paths for clarity

**Remember:**
- Stateful = Simpler commands
- Background = Non-blocking
- Sessions = Isolation
- Cleanup = Good practice

---

**Last Updated:** 2024-12-25  
**Version:** 1.0  
**Related Docs:**
- STATEFUL_SANDBOX_IMPLEMENTATION.md
- OPENHANDS_INTEGRATION.md
