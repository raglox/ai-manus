I'll gather more context about the existing sandbox implementation to create a comprehensive design.

<function_calls>
<invoke name="codebase_search">
<parameter name="query">sandbox configuration settings environment variables</parameter>
<parameter name="path">backend</parameter>
</invoke>
</function_calls>

<function_calls>
<invoke name="read_file">
<parameter name="args">
  <file>
    <path>backend/app/core/config.py</path>
  </file>
</invoke>
</function_calls>

<function_calls>
<invoke name="search_files">
<parameter name="path">backend</parameter>
<parameter name="regex">sandbox.*factory|get_sandbox</parameter>
<parameter name="file_pattern">*.py</parameter>
</invoke>
</function_calls>

<function_calls>
<invoke name="update_todo_list">
<parameter name="todos">
[ ] Analyze current sandbox implementation and interface requirements
[ ] Design CloudRunJobsSandbox architecture
[ ] Document state management strategy
[ ] Design API flow and execution pipeline
[ ] Define security model and isolation guarantees
[ ] Create implementation phases
[ ] Document testing strategy
[ ] Write comprehensive design document
</parameter>
</invoke>
</function_calls>

Now let me create the comprehensive design document:

<function_calls>
<invoke name="write_to_file">
<parameter name="path">plans/CLOUDRUN_JOBS_SANDBOX_DESIGN.md</parameter>
<parameter name="content"># Cloud Run Jobs Sandbox Architecture Design

**Date**: 2025-12-28  
**Author**: Architecture Mode  
**Status**: Design Phase  
**Purpose**: Replace failing [`DockerSandbox`](../backend/app/infrastructure/external/sandbox/docker_sandbox.py) with Cloud Run Jobs implementation

---

## Executive Summary

This document provides a comprehensive technical design for [`CloudRunJobsSandbox`](../backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py), a Cloud Run Jobs-based replacement for the Docker-in-Docker sandbox that fails in Cloud Run environments.

**Key Design Decisions:**
- ✅ Use Cloud Run Jobs for isolated command execution
- ✅ Cloud Storage for session state persistence
- ✅ Executor container pattern for command execution
- ✅ Asynchronous job execution with polling/webhooks
- ✅ Service account isolation for security
- ✅ Implement full [`Sandbox`](../backend/app/domain/external/sandbox.py) protocol compatibility

**Expected Benefits:**
- 🎯 Works in Cloud Run production environment
- 🎯 True process isolation via gVisor
- 🎯 Cost-effective serverless architecture (~$5/month)
- 🎯 Auto-scaling from zero
- 🎯 Enhanced security via IAM

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [State Management Strategy](#state-management-strategy)
5. [API Flow](#api-flow)
6. [Security Model](#security-model)
7. [Error Handling](#error-handling)
8. [Implementation Phases](#implementation-phases)
9. [Testing Strategy](#testing-strategy)
10. [Performance Considerations](#performance-considerations)
11. [Migration Plan](#migration-plan)

---

## Problem Statement

### Current Implementation Issues

The [`DockerSandbox`](../backend/app/infrastructure/external/sandbox/docker_sandbox.py:65) uses Docker-in-Docker which **fails in Cloud Run** because:

```python
# backend/app/infrastructure/external/sandbox/docker_sandbox.py:427
docker_client = docker.from_env()  # ❌ Fails - no Docker socket
container = docker_client.containers.run(...)  # ❌ Cannot create containers
```

**Root Causes:**
1. Cloud Run does not provide `/var/run/docker.sock` access
2. gVisor isolation prevents nested containers
3. No privileged mode support in Cloud Run
4. Security sandbox restrictions prevent container creation

### Requirements from Sandbox Protocol

The [`Sandbox`](../backend/app/domain/external/sandbox.py:6) protocol defines 40+ methods including:

**Core Execution:**
- `exec_command_stateful()` - Execute commands with state preservation
- `wait_for_process()` - Wait for command completion
- `kill_process()` - Terminate running processes

**State Management:**
- `list_background_processes()` - Track background jobs
- `kill_background_process()` - Manage background processes
- `get_background_logs()` - Retrieve process logs

**File Operations:**
- `file_read()`, `file_write()`, `file_delete()`
- `file_upload()`, `file_download()`
- `file_search()`, `file_find()`, `file_replace()`

**Session Lifecycle:**
- `create()` - Create new sandbox
- `destroy()` - Cleanup resources
- `ensure_sandbox()` - Health checks

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cloud Run Main Service                       │
│                  (FastAPI Backend Application)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Uses
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CloudRunJobsSandbox                           │
│                  (Sandbox Protocol Implementation)               │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Job Manager │  │ State Manager│  │  Result Retriever  │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└───────────┬────────────────┬─────────────────┬──────────────────┘
            │                │                 │
            ▼                ▼                 ▼
┌─────────────────┐  ┌──────────────┐  ┌────────────────────┐
│  Cloud Run Jobs │  │Cloud Storage │  │  Cloud Pub/Sub     │
│    Executor     │  │ State Bucket │  │   (optional)       │
│                 │  │              │  │                    │
│ ┌─────────────┐ │  │ ┌──────────┐ │  │  ┌──────────────┐ │
│ │  Executor   │ │  │ │ Sessions │ │  │  │ Completion   │ │
│ │  Container  │ │  │ │   State  │ │  │  │  Webhooks    │ │
│ │             │ │  │ └──────────┘ │  │  └──────────────┘ │
│ └─────────────┘ │  │ ┌──────────┐ │  └────────────────────┘
│                 │  │ │ Results  │ │
│                 │  │ │  Data    │ │
│                 │  │ └──────────┘ │
└─────────────────┘  └──────────────┘
```

### Component Responsibilities

**CloudRunJobsSandbox** (Main Class)
- Implements `Sandbox` protocol
- Manages job lifecycle
- Coordinates state persistence
- Handles result retrieval

**Job Manager**
- Creates Cloud Run Job definitions
- Triggers job executions
- Monitors execution status
- Handles job cleanup

**State Manager**
- Persists session state to Cloud Storage
- Loads session state for executions
- Manages session cleanup
- Tracks background processes

**Executor Container**
- Runs in Cloud Run Job
- Loads session state
- Executes commands
- Saves results and new state

---

## Core Components

### 1. CloudRunJobsSandbox Class

```python
# backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py

from google.cloud import run_v2
from google.cloud import storage
from typing import Dict, Any, Optional, List
import asyncio
import uuid
import json

class CloudRunJobsSandbox:
    """
    Cloud Run Jobs-based sandbox implementation.
    
    Replaces DockerSandbox for Cloud Run deployment where
    Docker-in-Docker is not available.
    """
    
    def __init__(
        self,
        project_id: str,
        region: str = "us-central1",
        executor_image: str = None,
        state_bucket: str = None
    ):
        """
        Initialize Cloud Run Jobs sandbox.
        
        Args:
            project_id: GCP project ID
            region: GCP region for job execution
            executor_image: Container image for executor
            state_bucket: Cloud Storage bucket for state
        """
        self.project_id = project_id
        self.region = region
        self.executor_image = executor_image or self._default_executor_image()
        self.state_bucket = state_bucket or f"{project_id}-sandbox-sessions"
        
        # Initialize clients
        self.job_client = run_v2.JobsClient()
        self.storage_client = storage.Client()
        self.executions_client = run_v2.ExecutionsClient()
        
        # Session management
        self._sandbox_id = str(uuid.uuid4())
        self._sessions = {}
        
    def _default_executor_image(self) -> str:
        """Get default executor container image"""
        return f"gcr.io/{self.project_id}/sandbox-executor:latest"
    
    @property
    def id(self) -> str:
        """Sandbox ID"""
        return self._sandbox_id
```

### 2. Session State Manager

```python
class SessionStateManager:
    """
    Manages session state in Cloud Storage.
    
    State Structure:
    - sessions/{session_id}/state.json - Current state
    - sessions/{session_id}/history/ - Execution history
    - executions/{execution_id}/ - Execution results
    """
    
    def __init__(self, storage_client: storage.Client, bucket_name: str):
        self.storage_client = storage_client
        self.bucket = storage_client.bucket(bucket_name)
        
    async def load_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Load session state from Cloud Storage.
        
        Returns:
            Session state dict with:
            - cwd: Current working directory
            - env_vars: Environment variables
            - background_pids: Background process tracking
            - created_at: Session creation timestamp
        """
        blob = self.bucket.blob(f"sessions/{session_id}/state.json")
        
        if not blob.exists():
            # Initialize new session
            return {
                "session_id": session_id,
                "cwd": "/workspace",
                "env_vars": {},
                "background_pids": {},
                "created_at": datetime.utcnow().isoformat()
            }
        
        state_json = blob.download_as_text()
        return json.loads(state_json)
    
    async def save_session_state(
        self, 
        session_id: str, 
        state: Dict[str, Any]
    ) -> None:
        """Save session state to Cloud Storage"""
        blob = self.bucket.blob(f"sessions/{session_id}/state.json")
        blob.upload_from_string(
            json.dumps(state, indent=2),
            content_type="application/json"
        )
    
    async def save_execution_result(
        self,
        execution_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Save execution result for retrieval"""
        blob = self.bucket.blob(f"executions/{execution_id}/result.json")
        blob.upload_from_string(
            json.dumps(result, indent=2),
            content_type="application/json"
        )
```

### 3. Job Manager

```python
class CloudRunJobManager:
    """
    Manages Cloud Run Job lifecycle.
    """
    
    def __init__(
        self,
        job_client: run_v2.JobsClient,
        executions_client: run_v2.ExecutionsClient,
        project_id: str,
        region: str
    ):
        self.job_client = job_client
        self.executions_client = executions_client
        self.project_id = project_id
        self.region = region
        self.parent = f"projects/{project_id}/locations/{region}"
    
    async def create_and_run_job(
        self,
        execution_id: str,
        command: str,
        session_id: str,
        executor_image: str,
        timeout: int = 120,
        memory: str = "512Mi",
        cpu: str = "1"
    ) -> str:
        """
        Create ephemeral job and trigger execution.
        
        Returns:
            Execution name for status tracking
        """
        job_name = f"sandbox-{execution_id[:8]}"
        
        # Create job definition
        job = run_v2.Job(
            name=f"{self.parent}/jobs/{job_name}",
            template=run_v2.ExecutionTemplate(
                template=run_v2.TaskTemplate(
                    containers=[run_v2.Container(
                        image=executor_image,
                        env=[
                            run_v2.EnvVar(name="EXECUTION_ID", value=execution_id),
                            run_v2.EnvVar(name="SESSION_ID", value=session_id),
                            run_v2.EnvVar(name="COMMAND", value=command),
                            run_v2.EnvVar(name="PROJECT_ID", value=self.project_id),
                        ],
                        resources=run_v2.ResourceRequirements(
                            limits={"memory": memory, "cpu": cpu}
                        )
                    )],
                    timeout=f"{timeout}s",
                    max_retries=0,  # No retries for sandbox execution
                    service_account=f"automation@{self.project_id}.iam.gserviceaccount.com"
                )
            )
        )
        
        # Create job
        operation = await asyncio.to_thread(
            self.job_client.create_job,
            parent=self.parent,
            job=job,
            job_id=job_name
        )
        
        # Wait for job creation
        job = await asyncio.to_thread(operation.result)
        
        # Execute job
        execution = await asyncio.to_thread(
            self.job_client.run_job,
            name=job.name
        )
        
        return execution.name
```

### 4. Executor Container

The executor runs inside Cloud Run Jobs and performs the actual command execution.

**Dockerfile:**
```dockerfile
# sandbox-executor/Dockerfile
FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    vim \
    nodejs \
    npm \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK (for storage access)
RUN pip install --no-cache-dir \
    google-cloud-storage==2.14.0 \
    google-cloud-logging==3.9.0

# Copy executor script
COPY executor.py /usr/local/bin/executor.py
RUN chmod +x /usr/local/bin/executor.py

# Create non-root user
RUN useradd -m -u 1000 sandbox && \
    chown -R sandbox:sandbox /workspace

USER sandbox

ENTRYPOINT ["python", "/usr/local/bin/executor.py"]
```

**Executor Script:**
```python
# sandbox-executor/executor.py
"""
Executor script that runs inside Cloud Run Job.
Loads state, executes command, saves results.
"""
import os
import sys
import json
import subprocess
import traceback
from datetime import datetime
from google.cloud import storage
from pathlib import Path

def load_state(storage_client, bucket_name, session_id):
    """Load session state from Cloud Storage"""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"sessions/{session_id}/state.json")
    
    if not blob.exists():
        return {
            "cwd": "/workspace",
            "env_vars": {},
            "background_pids": {}
        }
    
    return json.loads(blob.download_as_text())

def save_result(storage_client, bucket_name, execution_id, result):
    """Save execution result to Cloud Storage"""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"executions/{execution_id}/result.json")
    blob.upload_from_string(
        json.dumps(result, indent=2),
        content_type="application/json"
    )

def execute_command(command, state, timeout):
    """Execute command with state applied"""
    # Change to session CWD
    os.chdir(state["cwd"])
    
    # Apply environment variables
    env = os.environ.copy()
    env.update(state["env_vars"])
    
    # Check for background process
    is_background = command.strip().endswith('&')
    if is_background:
        command = command.strip()[:-1].strip()
        # Redirect output for background process
        command = f"nohup {command} > /tmp/bg_$$.out 2>&1 & echo $!"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        
        # Capture new state
        new_state = {
            "cwd": os.getcwd(),
            "env_vars": dict(os.environ),
            "background_pids": state["background_pids"].copy()
        }
        
        # Handle background PID
        background_pid = None
        if is_background and result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines and lines[0].isdigit():
                background_pid = int(lines[0])
                new_state["background_pids"][command] = background_pid
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "new_state": new_state,
            "background_pid": background_pid,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timeout after {timeout} seconds",
            "new_state": state,
            "background_pid": None,
            "completed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}\n{traceback.format_exc()}",
            "new_state": state,
            "background_pid": None,
            "completed_at": datetime.utcnow().isoformat()
        }

def main():
    # Get environment variables
    execution_id = os.environ.get("EXECUTION_ID")
    session_id = os.environ.get("SESSION_ID")
    command = os.environ.get("COMMAND")
    project_id = os.environ.get("PROJECT_ID")
    timeout = int(os.environ.get("TIMEOUT", "120"))
    
    if not all([execution_id, session_id, command, project_id]):
        print("ERROR: Missing required environment variables", file=sys.stderr)
        sys.exit(1)
    
    bucket_name = f"{project_id}-sandbox-sessions"
    
    try:
        # Initialize storage client
        storage_client = storage.Client()
        
        # Load session state
        state = load_state(storage_client, bucket_name, session_id)
        
        # Execute command
        result = execute_command(command, state, timeout)
        
        # Save result
        save_result(storage_client, bucket_name, execution_id, result)
        
        # Save updated state
        bucket = storage_client.bucket(bucket_name)
        state_blob = bucket.blob(f"sessions/{session_id}/state.json")
        state_blob.upload_from_string(
            json.dumps(result["new_state"], indent=2),
            content_type="application/json"
        )
        
        print(f"✅ Execution {execution_id} completed successfully")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Execution failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## State Management Strategy

### State Storage Structure

```
gs://{project-id}-sandbox-sessions/
├── sessions/
│   ├── {session-id}/
│   │   ├── state.json              # Current session state
│   │   ├── history/
│   │   │   ├── {timestamp}.json    # State snapshots
│   │   └── files/                  # Uploaded files
│   │       └── {file-path}
├── executions/
│   └── {execution-id}/
│       ├── result.json              # Execution result
│       └── logs.txt                 # Execution logs
└── background/
    └── {pid}/
        └── output.log               # Background process logs
```

### Session State Schema

```json
{
  "session_id": "default",
  "cwd": "/workspace/project",
  "env_vars": {
    "USER": "sandbox",
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "PYTHONPATH": "/workspace/lib"
  },
  "background_pids": {
    "python -m http.server 8000": 12345
  },
  "created_at": "2025-12-28T09:00:00Z",
  "last_updated": "2025-12-28T09:15:30Z",
  "execution_count": 15
}
```

### Execution Result Schema

```json
{
  "execution_id": "exec-abc123",
  "session_id": "default",
  "command": "ls -la",
  "exit_code": 0,
  "stdout": "total 48\ndrwxr-xr-x  5 sandbox sandbox 4096 Dec 28 09:15 .\n...",
  "stderr": "",
  "new_state": {
    "cwd": "/workspace/project",
    "env_vars": {...},
    "background_pids": {}
  },
  "background_pid": null,
  "started_at": "2025-12-28T09:15:25Z",
  "completed_at": "2025-12-28T09:15:30Z",
  "duration_seconds": 5
}
```

---

## API Flow

### Command Execution Flow

```mermaid
sequenceDiagram
    participant Client as FastAPI Client
    participant CRJ as CloudRunJobsSandbox
    participant SM as StateManager
    participant JM as JobManager
    participant CS as Cloud Storage
    participant Job as Cloud Run Job

    Client->>CRJ: exec_command_stateful("ls -la")
    CRJ->>SM: load_session_state(session_id)
    SM->>CS: Get sessions/{id}/state.json
    CS-->>SM: Return state
    SM-->>CRJ: Session state
    
    CRJ->>JM: create_and_run_job(command, state)
    JM->>Job: Create & Execute Job
    Job->>CS: Load state
    Job->>Job: Execute command
    Job->>CS: Save result & new state
    Job-->>JM: Execution complete
    
    JM->>CRJ: Execution name
    CRJ->>SM: poll_execution_result(execution_id)
    SM->>CS: Get executions/{id}/result.json
    CS-->>SM: Result data
    SM-->>CRJ: Execution result
    
    CRJ->>SM: save_session_state(new_state)
    SM->>CS: Update sessions/{id}/state.json
    
    CRJ-->>Client: ToolResult
```

### File Upload Flow

```mermaid
sequenceDiagram
    participant Client
    participant CRJ as CloudRunJobsSandbox
    participant CS as Cloud Storage
    participant Job as Cloud Run Job

    Client->>CRJ: file_upload(file_data, path)
    CRJ->>CS: Upload to sessions/{id}/files/{path}
    CS-->>CRJ: Upload complete
    
    CRJ->>Job: Create job with COPY command
    Job->>CS: Read from sessions/{id}/files/{path}
    Job->>Job: Copy to /workspace/{path}
    Job-->>CRJ: Copy complete
    
    CRJ-->>Client: ToolResult(success=True)
```

### Background Process Management

```mermaid
sequenceDiagram
    participant Client
    participant CRJ as CloudRunJobsSandbox
    participant Job1 as Job (Start)
    participant Job2 as Job (Monitor)
    participant CS as Cloud Storage

    Client->>CRJ: exec_command_stateful("server.py &")
    CRJ->>Job1: Execute with background flag
    Job1->>Job1: Start process, capture PID
    Job1->>CS: Save PID to state
    Job1-->>CRJ: Return PID=12345
    
    Note over CRJ: Later...
    Client->>CRJ: list_background_processes()
    CRJ->>CS: Load all session states
    CS-->>CRJ: Return PIDs list
    CRJ-->>Client: [{pid: 12345, running: true}]
    
    Note over CRJ: Check if still running
    Client->>CRJ: get_background_logs(12345)
    CRJ->>Job2: Execute "cat /tmp/bg_12345.out"
    Job2-->>CRJ: Log content
    CRJ-->>Client: Log data
```

---

## Security Model

### Isolation Guarantees

| Security Requirement | Implementation |
|---------------------|----------------|
| **Process Isolation** | Each execution in separate Cloud Run Job |
| **Resource Limits** | Job-level memory/CPU limits |
| **Network Isolation** | VPC connector + firewall rules |
| **File System Isolation** | Ephemeral job filesystem, state in Cloud Storage |
| **Credential Isolation** | Service account per job with minimal IAM |
| **Execution Timeout** | Configurable timeout (default 120s, max 3600s) |
| **Cleanup** | Auto-deletion of completed jobs |

### IAM Configuration

```yaml
# Required Service Account Roles
automation@{project}.iam.gserviceaccount.com:
  roles:
    - roles/run.admin                    # Create/manage jobs
    - roles/iam.serviceAccountUser       # Act as service account
    - roles/artifactregistry.reader      # Pull container images
    - roles/storage.objectAdmin          # Access state bucket
    - roles/logging.logWriter            # Write logs
    - roles/secretmanager.secretAccessor # Access secrets (if needed)
```

### Security Best Practices

1. **Minimal Permissions**
   - Job service account has NO project-level permissions
   - Only bucket-specific storage access
   - No ability to create other resources

2. **Binary Authorization**
   - Only signed images can execute
   - Container image vulnerability scanning

3. **Network Controls**
   - No external internet by default
   - VPC connector for internal resources
   - Egress firewall rules

4. **Audit Logging**
   - All job executions logged
   - State changes tracked
   - Access logs for Cloud Storage

5. **Secret Management**
   - Never pass secrets in environment variables
   - Use Secret Manager references
   - Rotate secrets regularly

---

## Error Handling

### Error Categories and Responses

#### 1. Job Creation Errors

```python
class JobCreationError(Exception):
    """Failed to create Cloud Run Job"""
    pass

# Handling
try:
    execution = await job_manager.create_and_run_job(...)
except JobCreationError as e:
    return ToolResult(
        success=False,
        message=f"Failed to create execution environment: {e}",
        data={"error_type": "job_creation"}
    )
```

#### 2. Execution Timeout

```python
# Timeout occurs in executor or polling
return {
    "exit_code": -1,
    "stdout": "",
    "stderr": "Execution timeout after 120 seconds",
    "timed_out": True
}
```

#### 3. State Management Errors

```python
class StateLoadError(Exception):
    """Failed to load session state"""
    pass

class StateSaveError(Exception):
    """Failed to save session state"""
    pass

# Retry logic
async def load_state_with_retry(session_id: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await state_manager.load_session_state(session_id)
        except Exception as e:
            if attempt == max_retries - 1:
                raise StateLoadError(f"Failed after {max_retries} attempts: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

#### 4. Resource Exhaustion

```python
# Job quota exceeded
if "Quota exceeded" in error_message:
    return ToolResult(
        success=False,
        message="Sandbox capacity limit reached. Please try again later.",
        data={"error_type": "quota_exceeded", "retry_after": 60}
    )
```

### Error Recovery Strategies

| Error Type | Recovery Strategy | Fallback |
|-----------|------------------|----------|
| Job creation failure | Retry with exponential backoff | Return error to user |
| Execution timeout | Kill job, return partial results | None |
| State load failure | Use default state | Create new session |
| State save failure | Retry 3 times | Log error, continue |
| Network errors | Retry with backoff | Fail gracefully |
| Quota exceeded | Queue request | Return rate limit error |

---

## Implementation Phases

### Phase 1: Core Execution Engine (Week 1-2)

**Goal**: Basic command execution working

**Tasks**:
- [ ] Create `CloudRunJobsSandbox` class structure
- [ ] Implement `exec_command_stateful()` method
- [ ] Build executor container and Dockerfile
- [ ] Implement basic state loading/saving
- [ ] Create job creation and execution logic
- [ ] Test with simple commands (echo, ls, pwd)

**Deliverables**:
- Working `exec_command_stateful()` for simple commands
- Executor container image in Artifact Registry
- Basic state persistence in Cloud Storage

**Success Criteria**:
```python
sandbox = CloudRunJobsSandbox.create()
result = await sandbox.exec_command_stateful("echo Hello")
assert result["exit_code"] == 0
assert "Hello" in result["stdout"]
```

### Phase 2: State Management (Week 2-3)

**Goal**: Stateful execution with CWD and ENV preservation

**Tasks**:
- [ ] Implement session state schema
- [ ] Add CWD preservation logic
- [ ] Add ENV variable tracking
- [ ] Implement `list_sessions()` method
- [ ] Add session cleanup logic
- [ ] Test state persistence across commands

**Deliverables**:
- Full state management system
- Session lifecycle methods
- State consistency guarantees

**Success Criteria**:
```python
sandbox = CloudRunJobsSandbox.create()
await sandbox.exec_command_stateful("cd /tmp")
result = await sandbox.exec_command_stateful("pwd")
assert "/tmp" in result["stdout"]
```

### Phase 3: Background Processes (Week 3-4)

**Goal**: Support for long-running background processes

**Tasks**:
- [ ] Implement background process detection
- [ ] Add PID tracking and persistence
- [ ] Implement `list_background_processes()`
- [ ] Implement `kill_background_process()`
- [ ] Implement `get_background_logs()`
- [ ] Test with long-running processes

**Deliverables**:
- Background process management
- Process monitoring and logging
- Cleanup mechanisms

**Success Criteria**:
```python
result = await sandbox.exec_command_stateful("sleep 100 &")
pid = result["background_pid"]
processes = await sandbox.list_background_processes()
assert any(p["pid"] == pid for p in processes)
```

### Phase 4: File Operations (Week 4-5)

**Goal**: Complete file operation support

**Tasks**:
- [ ] Implement `file_read()`, `file_write()`, `file_delete()`
- [ ] Implement `file_upload()` and `file_download()`
- [ ] Implement `file_list()`, `file_search()`, `file_find()`
- [ ] Add large file handling (streaming)
- [ ] Test file operations thoroughly

**Deliverables**:
- All file operation methods implemented
- Upload/download with progress tracking
- File size limits and validation

**Success Criteria**:
```python
await sandbox.file_write("/tmp/test.txt", "content")
result = await sandbox.file_read("/tmp/test.txt")
assert result.data["content"] == "content"
```

### Phase 5: Integration & Testing (Week 5-6)

**Goal**: Replace DockerSandbox in production

**Tasks**:
- [ ] Create sandbox factory with environment detection
- [ ] Integration testing with agent workflows
- [ ] Performance benchmarking
- [ ] Load testing (concurrent executions)
- [ ] Documentation updates
- [ ] Deployment to staging

**Deliverables**:
- Drop-in replacement for DockerSandbox
- Comprehensive test suite
- Performance metrics
- Deployment guide

**Success Criteria**:
- All existing agent tests pass
- Performance within acceptable range
- No regressions in functionality

### Phase 6: Production Deployment (Week 6-7)

**Goal**: Live in production

**Tasks**:
- [ ] Deploy executor image to production
- [ ] Update Cloud Run service configuration
- [ ] Gradual rollout (canary deployment)
- [ ] Monitor metrics and errors
- [ ] Optimize based on production data

**Deliverables**:
- Production deployment
- Monitoring dashboards
- Incident response runbook
- Cost analysis

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_cloudrun_jobs_sandbox.py

import pytest
from unittest.mock import Mock, AsyncMock
from app.infrastructure.external.sandbox.cloudrun_jobs_sandbox import CloudRunJobsSandbox

@pytest.fixture
async def sandbox():
    return CloudRunJobsSandbox(
        project_id="test-project",
        region="us-central1",
        executor_image="gcr.io/test/executor:latest",
        state_bucket="test-bucket"
    )

class TestCloudRunJobsSandbox:
    async def test_exec_command_simple(self, sandbox):
        """Test simple command execution"""
        result = await sandbox.exec_command_stateful("echo test")
        
        assert result["exit_code"] == 0
        assert "test" in result["stdout"]
        assert result["session_id"] == "default"
    
    async def test_exec_command_with_cwd(self, sandbox):
        """Test CWD preservation"""
        await sandbox.exec_command_stateful("cd /tmp")
        result = await sandbox.exec_command_stateful("pwd")
        
        assert "/tmp" in result["stdout"]
    
    async def test_background_process(self, sandbox):
        """Test background process creation"""
        result = await sandbox.exec_command_stateful("sleep 100 &")
        
        assert "background_pid" in result
        assert result["background_pid"] is not None
    
    async def test_session_isolation(self, sandbox):
        """Test session isolation"""
        await sandbox.exec_command_stateful("cd /tmp", session_id="session1")
        result = await sandbox.exec_command_stateful("pwd", session_id="session2")
        
        assert "/tmp" not in result["stdout"]  # Different session
```

### Integration Tests

```python
# tests/integration/test_sandbox_integration.py

@pytest.mark.integration
class TestSandboxIntegration:
    async def test_real_job_execution(self):
        """Test actual Cloud Run Job execution"""
        sandbox = await CloudRunJobsSandbox.create()
        
        result = await sandbox.exec_command_stateful("ls -la")
        assert result["exit_code"] == 0
        
        await sandbox.destroy()
    
    async def test_state_persistence(self):
        """Test state persistence across executions"""
        sandbox = await CloudRunJobsSandbox.create()
        
        await sandbox.exec_command_stateful("export TEST_VAR=value123")
        result = await sandbox.exec_command_stateful("echo $TEST_VAR")
        
        assert "value123" in result["stdout"]
        await sandbox.destroy()
```

### Performance Tests

```python
# tests/performance/test_sandbox_performance.py

@pytest.mark.performance
class TestSandboxPerformance:
    async def test_cold_start_latency(self):
        """Measure cold start time"""
        start = time.time()
        sandbox = await CloudRunJobsSandbox.create()
        await sandbox.exec_command_stateful("echo test")
        duration = time.time() - start
        
        assert duration < 5.0  # Max 5 seconds cold start
        await sandbox.destroy()
    
    async def test_concurrent_executions(self):
        """Test concurrent command execution"""
        sandbox = await CloudRunJobsSandbox.create()
        
        tasks = [
            sandbox.exec_command_stateful(f"echo test{i}", session_id=f"s{i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        assert all(r["exit_code"] == 0 for r in results)
        await sandbox.destroy()
```

### Test Coverage Goals

- **Unit Tests**: 85%+ coverage
- **Integration Tests**: All critical paths
- **Performance Tests**: Cold start, concurrent execution, state persistence
- **Security Tests**: IAM validation, network isolation, resource limits

---

## Performance Considerations

### Latency Breakdown

| Operation | Expected Latency | Optimization |
|-----------|-----------------|--------------|
| Job creation | 0.5-1s | Reuse job templates |
| Cold start | 2-5s | Pre-warmed containers (future) |
| Command execution | Variable | Timeout limits |
| State load/save | 100-200ms | Caching, compression |
| Result retrieval | 100-300ms | Polling interval tuning |
| **Total (cold)** | **3-7s** | Acceptable for agent use case |
| **Total (warm)** | **0.5-2s** | Reuse jobs if possible |

### Optimization Strategies

1. **Job Template Reuse**
   - Create reusable job templates
   - Only update environment variables
   - Reduce job creation overhead

2. **Parallel Execution**
   - Multiple sessions = multiple concurrent jobs
   - No shared state = natural parallelism

3. **State Caching**
   - Cache frequently accessed session states
   - Invalidate on write
   - Use Cloud Storage object versioning

4. **Result Streaming**
   - Stream large command outputs
   - Use Cloud Storage resumable uploads
   - Implement progress callbacks

5. **Background Process Optimization**
   - Dedicated long-running jobs for servers
   - WebSocket connections for real-time logs
   - Efficient PID tracking

---

## Migration Plan

### Pre-Migration Checklist

- [ ] GCP permissions configured (see [`GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md`](../../GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md))
- [ ] Executor container image built and deployed
- [ ] Cloud Storage bucket created with proper lifecycle policies
- [ ] Service account IAM roles assigned
- [ ] Monitoring and alerting configured

### Migration Strategy

**Option 1: Feature Flag (Recommended)**

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    use_cloudrun_jobs_sandbox: bool = Field(
        default=False,
        env="USE_CLOUDRUN_JOBS_SANDBOX"
    )

# backend/app/infrastructure/external/sandbox/factory.py
async def get_sandbox() -> Sandbox:
    settings = get_settings()
    
    if settings.use_cloudrun_jobs_sandbox:
        return await CloudRunJobsSandbox.create()
    else:
        return await DockerSandbox.create()
```

**Rollout Plan**:
1. Deploy with feature flag OFF (default to DockerSandbox)
2. Test in staging with flag ON
3. Enable for 10% of production traffic
4. Monitor metrics and errors
5. Gradually increase to 100%
6. Remove DockerSandbox after stable period

**Option 2: Environment-Based**

```python
async def get_sandbox() -> Sandbox:
    if settings.environment == "production":
        return await CloudRunJobsSandbox.create()
    else:
        return await DockerSandbox.create()  # Local development
```

### Rollback Plan

If critical issues occur:

1. **Immediate**: Set feature flag to OFF
2. **Short-term**: Route traffic back to DockerSandbox
3. **Analysis**: Investigate root cause
4. **Fix**: Address issues in CloudRunJobsSandbox
5. **Retry**: Attempt rollout again

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | >99.5% | Job success rate |
| Latency (p50) | <3s | Job execution time |
| Latency (p99) | <10s | Job execution time |
| Error rate | <1% | Failed jobs / total jobs |
| Cost | <$10/month | GCP billing |
| User satisfaction | No regression | Support tickets, feedback |

---

## Appendices

### A. Configuration Reference

```python
# backend/app/core/config.py (additions)

class Settings(BaseSettings):
    # Cloud Run Jobs Sandbox
    gcp_project_id: str = Field(env="GCP_PROJECT_ID")
    gcp_region: str = Field(default="us-central1", env="GCP_REGION")
    sandbox_executor_image: str = Field(
        env="SANDBOX_EXECUTOR_IMAGE",
        default_factory=lambda: f"gcr.io/{os.getenv('GCP_PROJECT_ID')}/sandbox-executor:latest"
    )
    sandbox_state_bucket: str = Field(
        env="SANDBOX_STATE_BUCKET",
        default_factory=lambda: f"{os.getenv('GCP_PROJECT_ID')}-sandbox-sessions"
    )
    sandbox_job_timeout: int = Field(default=120, env="SANDBOX_JOB_TIMEOUT")
    sandbox_job_memory: str = Field(default="512Mi", env="SANDBOX_JOB_MEMORY")
    sandbox_job_cpu: str = Field(default="1", env="SANDBOX_JOB_CPU")
```

### B. Monitoring Queries

```sql
-- Cloud Logging: Job execution success rate
resource.type="cloud_run_job"
resource.labels.job_name=~"sandbox-.*"
severity>=ERROR

-- Cloud Monitoring: Execution latency
fetch cloud_run_job
| metric 'run.googleapis.com/job/completed_executions'
| align rate(1m)
| group_by [resource.job_name]

-- Cloud Storage: State access patterns
resource.type="gcs_bucket"
resource.labels.bucket_name="*-sandbox-sessions"
protoPayload.methodName="storage.objects.get"
```

### C. Cost Estimation

**Monthly Cost Breakdown** (1000 executions/day):

| Component | Unit Cost | Usage | Monthly Cost |
|-----------|-----------|-------|--------------|
| Cloud Run Jobs vCPU | $0.00002400/vCPU-sec | 150k sec | $3.60 |
| Cloud Run Jobs Memory | $0.00000250/GB-sec | 75k GB-sec | $0.19 |
| Cloud Storage (state) | $0.020/GB | 10 GB | $0.20 |
| Cloud Storage (operations) | $0.004/10k ops | 60k ops | $0.02 |
| Network egress | $0.12/GB | 1 GB | $0.12 |
| **Total** | | | **~$4.13/month** |

**Comparison**:
- Current DockerSandbox: $0 (doesn't work)
- GKE Autopilot: ~$75/month
- Cloud Functions: ~$2/month (limited runtime)
- Cloud Run Jobs: ~$4/month ✅ **Best value**

---

## Conclusion

The CloudRunJobsSandbox design provides a robust, scalable, and cost-effective replacement for the failing DockerSandbox implementation. Key benefits include:

✅ **Functional**: Works in Cloud Run production environment  
✅ **Secure**: Enhanced isolation via gVisor + IAM  
✅ **Scalable**: Serverless auto-scaling from zero  
✅ **Cost-effective**: ~$4/month vs $75+ for alternatives  
✅ **Maintainable**: Simple architecture, minimal ops overhead  

**Next Steps**:
1. Review and approve this design
2. Begin Phase 1 implementation (Core Execution Engine)
3. Iterate based on testing and feedback
4. Deploy to production with gradual rollout

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-28  
**Status**: Ready for Review
</parameter>
</invoke>
</function_calls>

Now let me update the todo list to mark progress:

<function_calls>
<invoke name="update_todo_list">
<parameter name="todos">
[x] Analyze current sandbox implementation and interface requirements
[x] Design CloudRunJobsSandbox architecture
[x] Document state management strategy
[x] Design API flow and execution pipeline
[x] Define security model and isolation guarantees
[x] Create implementation phases
[x] Document testing strategy
[x] Write comprehensive design document
</parameter>
</invoke>
</function_calls>

<function_calls>
<invoke name="attempt_completion">
<parameter name="result">
I've completed the CloudRunJobsSandbox architecture design to replace the failing DockerSandbox. The comprehensive design document has been created at [`plans/CLOUDRUN_JOBS_SANDBOX_DESIGN.md`](plans/CLOUDRUN_JOBS_SANDBOX_DESIGN.md).

## Design Highlights

**Architecture Overview:**
- Cloud Run Jobs for isolated command execution (replaces Docker-in-Docker)
- Cloud Storage for session state persistence
- Executor container pattern for command execution
- Full compatibility with the [`Sandbox`](backend/app/domain/external/sandbox.py:6) protocol interface

**Key Components:**
1. **CloudRunJobsSandbox** - Main class implementing Sandbox protocol
2. **SessionStateManager** - Manages state in Cloud Storage
3. **CloudRunJobManager** - Handles job lifecycle
4. **Executor Container** - Python container that runs commands

**State Management:**
- Session state stored in Cloud Storage (CWD, ENV vars, background PIDs)
- Execution results cached for retrieval
- Background process tracking and log access

**Security Model:**
- gVisor kernel-level isolation per job
- Minimal IAM permissions via service account
- Resource limits (memory, CPU, timeout)
- Automatic job cleanup after completion

**Performance:**
- Cold start: 3-7 seconds (acceptable for agent use case)
- Warm execution: 0.5-2 seconds
- Cost: ~$4/month (vs $75+ for GKE alternatives)

**Implementation Plan:**
- **Phase 1** (Weeks 1-2): Core execution engine
- **Phase 2** (Weeks 2-3): State management
- **Phase 3** (Weeks 3-4): Background processes
- **Phase 4** (Weeks 4-5): File operations
- **Phase 5** (Weeks 5-6): Integration & testing
- **Phase 6** (Weeks 6-7): Production deployment

The design document includes detailed implementation code, API flows, security considerations, error handling strategies, testing plans, and a migration roadmap. All necessary GCP permissions have been documented in [`GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md`](GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md).
</parameter>
</invoke>
</function_calls>