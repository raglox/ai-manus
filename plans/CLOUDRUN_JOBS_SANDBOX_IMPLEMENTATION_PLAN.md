# Cloud Run Jobs Sandbox Implementation Plan

**Document Version**: 1.0  
**Date**: 2025-12-28  
**Status**: Ready for Review  
**Author**: Architect Mode

---

## Executive Summary

This document provides a **strict, fail-safe implementation plan** for migrating from [`DockerSandbox`](../backend/app/infrastructure/external/sandbox/docker_sandbox.py) to [`CloudRunJobsSandbox`](../backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py) without breaking production.

**Critical Constraints:**
- ⛔ **DO NOT modify existing DockerSandbox code** (production dependency)
- ✅ **Implement CloudRunJobsSandbox as NEW class** (side-by-side)
- ✅ **Use feature flags** for gradual rollout
- ✅ **Comprehensive testing** at every phase
- ✅ **Rollback capability** at all times
- ✅ **Zero-downtime migration**

**Timeline**: 6-8 weeks with validation checkpoints

---

## Table of Contents

1. [Risk Assessment](#risk-assessment)
2. [Prerequisites](#prerequisites)
3. [Implementation Phases](#implementation-phases)
4. [Testing Strategy](#testing-strategy)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring & Validation](#monitoring--validation)
7. [Migration Checklist](#migration-checklist)

---

## Risk Assessment

### High-Risk Areas

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Breaking DockerSandbox** | 🔴 Critical | Low | Never modify existing code; implement separately |
| **State loss during migration** | 🔴 Critical | Medium | Comprehensive state persistence testing |
| **Background process tracking failure** | 🟡 High | Medium | Extensive background process tests |
| **File operations corruption** | 🟡 High | Low | Upload/download validation in every phase |
| **Integration test failures** | 🟡 High | Medium | Run full test suite after each change |
| **GCP permission issues** | 🟡 High | Medium | Pre-validate all IAM permissions |
| **Cost overruns** | 🟢 Medium | Low | Set billing alerts and quotas |
| **Performance degradation** | 🟢 Medium | Medium | Benchmark against DockerSandbox baseline |

### Risk Mitigation Strategy

**Principle**: **Test Early, Test Often, Never Assume**

1. **Isolation**: Build CloudRunJobsSandbox in isolation, never touching DockerSandbox
2. **Parallel Testing**: Run both implementations side-by-side during validation
3. **Feature Flags**: Use environment variables to control rollout
4. **Gradual Rollout**: Start with 0%, increase to 1%, 10%, 50%, 100%
5. **Monitoring**: Track all metrics continuously during migration
6. **Immediate Rollback**: Single environment variable change to revert

---

## Prerequisites

### Phase 0: Environment Setup (Week 0)

**Goal**: Prepare GCP environment and validate permissions

#### Tasks

- [ ] **GCP Project Setup**
  - [ ] Verify GCP project ID and region configuration
  - [ ] Enable required APIs:
    ```bash
    gcloud services enable run.googleapis.com
    gcloud services enable storage.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    gcloud services enable logging.googleapis.com
    ```
  - [ ] Create Cloud Storage bucket for session state:
    ```bash
    gsutil mb -l us-central1 gs://${PROJECT_ID}-sandbox-sessions
    gsutil lifecycle set lifecycle.json gs://${PROJECT_ID}-sandbox-sessions
    ```

- [ ] **IAM Configuration**
  - [ ] Create service account for Cloud Run Jobs:
    ```bash
    gcloud iam service-accounts create sandbox-executor \
      --display-name="Sandbox Executor Service Account"
    ```
  - [ ] Assign required roles (see [`GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md`](../GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md))
  - [ ] Test service account permissions:
    ```bash
    ./scripts/test_iam_permissions.sh
    ```

- [ ] **Configuration Updates**
  - [ ] Add configuration to [`backend/app/core/config.py`](../backend/app/core/config.py):
    ```python
    # Cloud Run Jobs Sandbox Configuration
    use_cloudrun_jobs_sandbox: bool = False  # Feature flag
    gcp_project_id: str | None = None
    gcp_region: str = "us-central1"
    sandbox_executor_image: str | None = None
    sandbox_state_bucket: str | None = None
    sandbox_job_timeout: int = 120
    sandbox_job_memory: str = "512Mi"
    sandbox_job_cpu: str = "1"
    ```
  - [ ] Update `.env.example` with new configuration variables

- [ ] **Baseline Metrics**
  - [ ] Run existing test suite and record baseline:
    ```bash
    pytest backend/tests/unit/test_docker_sandbox.py -v --durations=10
    pytest backend/tests/integration/test_sandbox_integration.py -v
    ```
  - [ ] Document current performance metrics
  - [ ] Record current test coverage percentage

#### Validation Checkpoint

**Exit Criteria:**
- ✅ All GCP APIs enabled
- ✅ IAM permissions validated
- ✅ Cloud Storage bucket created and accessible
- ✅ Configuration added without breaking existing code
- ✅ All existing tests pass with 0 failures
- ✅ Baseline metrics documented

**Rollback**: Remove configuration additions (safe, no production impact)

---

## Implementation Phases

### Phase 1: Core Executor Container (Week 1-2)

**Goal**: Build and test the executor container that runs commands in Cloud Run Jobs

#### Tasks

1. **Create Executor Dockerfile**
   - [ ] Create `backend/sandbox-executor/Dockerfile`:
     ```dockerfile
     FROM python:3.12-slim
     
     WORKDIR /workspace
     
     # Install system dependencies
     RUN apt-get update && apt-get install -y \
         curl git wget vim nodejs npm build-essential \
         && rm -rf /var/lib/apt/lists/*
     
     # Install Google Cloud SDK
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

2. **Create Executor Script**
   - [ ] Create `backend/sandbox-executor/executor.py` with:
     - State loading from Cloud Storage
     - Command execution with CWD/ENV preservation
     - Result saving to Cloud Storage
     - Error handling and logging

3. **Build and Deploy Executor Image**
   - [ ] Create `backend/sandbox-executor/build.sh`:
     ```bash
     #!/bin/bash
     set -e
     
     PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
     IMAGE_NAME="gcr.io/${PROJECT_ID}/sandbox-executor"
     
     echo "Building executor image..."
     docker build -t ${IMAGE_NAME}:latest .
     
     echo "Pushing to GCR..."
     docker push ${IMAGE_NAME}:latest
     
     echo "✅ Executor image deployed: ${IMAGE_NAME}:latest"
     ```
   - [ ] Test executor locally with Docker:
     ```bash
     docker run --rm \
       -e EXECUTION_ID=test-exec \
       -e SESSION_ID=test-session \
       -e COMMAND="echo hello" \
       -e PROJECT_ID=${PROJECT_ID} \
       ${IMAGE_NAME}:latest
     ```

4. **Create CloudRunJobsSandbox Class Structure**
   - [ ] Create `backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py`
   - [ ] Implement `__init__()` and basic setup
   - [ ] Implement `id`, `cdp_url`, `vnc_url` properties (stub implementations)
   - [ ] Add comprehensive docstrings

5. **Unit Tests**
   - [ ] Create `backend/tests/unit/test_cloudrun_jobs_sandbox.py`
   - [ ] Test initialization
   - [ ] Test configuration parsing
   - [ ] Test GCP client creation
   - [ ] Mock all GCP API calls

#### Validation Checkpoint

**Tests to Pass:**
```bash
# Unit tests must pass
pytest backend/tests/unit/test_cloudrun_jobs_sandbox.py -v

# Existing tests must still pass (no regression)
pytest backend/tests/unit/test_docker_sandbox.py -v
```

**Manual Validation:**
- [ ] Executor container builds successfully
- [ ] Executor container pushed to GCR
- [ ] Can pull executor image from GCR
- [ ] Executor runs successfully with test command
- [ ] CloudRunJobsSandbox class instantiates without errors

**Rollback**: Delete `cloudrun_jobs_sandbox.py` and executor files (safe, not integrated)

---

### Phase 2: Job Management & Execution (Week 2-3)

**Goal**: Implement job creation, execution, and result retrieval

#### Tasks

1. **Implement Job Manager**
   - [ ] Add `CloudRunJobManager` class to handle:
     - Job creation with Cloud Run Jobs API
     - Job execution triggering
     - Execution monitoring and status polling
     - Job cleanup after completion
   - [ ] Implement exponential backoff for API retries
   - [ ] Add comprehensive error handling

2. **Implement State Manager**
   - [ ] Add `SessionStateManager` class to handle:
     - Session state loading from Cloud Storage
     - Session state saving with versioning
     - Execution result storage
     - State schema validation
   - [ ] Implement state caching for performance
   - [ ] Add state consistency checks

3. **Implement `exec_command_stateful()`**
   - [ ] Core command execution flow:
     1. Load session state
     2. Create and trigger Cloud Run Job
     3. Poll for job completion
     4. Retrieve execution results
     5. Update session state
   - [ ] Handle background processes (commands ending with `&`)
   - [ ] Parse and preserve CWD changes
   - [ ] Parse and preserve ENV changes
   - [ ] Implement timeout handling

4. **Integration Tests**
   - [ ] Create `backend/tests/integration/test_cloudrun_jobs_sandbox_real.py`
   - [ ] Test actual job execution in GCP (marked with `@pytest.mark.integration`)
   - [ ] Test simple commands (echo, pwd, ls)
   - [ ] Test CWD preservation across commands
   - [ ] Test ENV preservation across commands

#### Validation Checkpoint

**Tests to Pass:**
```bash
# Unit tests
pytest backend/tests/unit/test_cloudrun_jobs_sandbox.py -v

# Integration tests (requires GCP)
pytest backend/tests/integration/test_cloudrun_jobs_sandbox_real.py -v -m integration

# No regression
pytest backend/tests/unit/test_docker_sandbox.py -v
```

**Manual Validation:**
- [ ] Can create Cloud Run Job successfully
- [ ] Can execute simple command and retrieve result
- [ ] CWD persists between commands in same session
- [ ] ENV vars persist between commands in same session
- [ ] Job cleanup happens after execution
- [ ] Performance: Cold start < 7s, warm < 2s

**Success Criteria:**
```python
# This must work
sandbox = await CloudRunJobsSandbox.create()
result = await sandbox.exec_command_stateful("echo hello")
assert result["exit_code"] == 0
assert "hello" in result["stdout"]

result2 = await sandbox.exec_command_stateful("cd /tmp && pwd")
result3 = await sandbox.exec_command_stateful("pwd")
assert "/tmp" in result3["stdout"]  # CWD preserved
```

**Rollback**: CloudRunJobsSandbox not yet integrated, safe to revert

---

### Phase 3: Background Process Management (Week 3-4)

**Goal**: Support long-running background processes with PID tracking

#### Tasks

1. **Implement Background Process Detection**
   - [ ] Detect commands ending with `&`
   - [ ] Capture PID from background process start
   - [ ] Store PID in session state
   - [ ] Redirect background process output to `/tmp/bg_$PID.out`

2. **Implement Process Management Methods**
   - [ ] `list_background_processes()` - List all tracked background processes
   - [ ] `kill_background_process()` - Kill process by PID/pattern/session
   - [ ] `get_background_logs()` - Retrieve background process logs
   - [ ] `_check_pid_running()` - Verify if process is still running

3. **Background Process Tests**
   - [ ] Test background process creation and PID capture
   - [ ] Test process status checking
   - [ ] Test process termination
   - [ ] Test log retrieval
   - [ ] Test cleanup on session close

#### Validation Checkpoint

**Tests to Pass:**
```bash
pytest backend/tests/unit/test_cloudrun_jobs_sandbox.py::TestBackgroundProcesses -v
pytest backend/tests/integration/test_cloudrun_jobs_sandbox_real.py::TestBackgroundProcesses -v
```

**Success Criteria:**
```python
# Background process must work
result = await sandbox.exec_command_stateful("sleep 100 &")
assert "background_pid" in result
pid = result["background_pid"]

processes = await sandbox.list_background_processes()
assert any(p["pid"] == pid for p in processes)

await sandbox.kill_background_process(pid=pid)
```

**Rollback**: Still not integrated, safe to revert

---

### Phase 4: File Operations (Week 4-5)

**Goal**: Implement all file operation methods from Sandbox protocol

#### Tasks

1. **Implement Core File Operations**
   - [ ] `file_read()` - Read file content
   - [ ] `file_write()` - Write file content
   - [ ] `file_delete()` - Delete file
   - [ ] `file_exists()` - Check file existence
   - [ ] `file_list()` - List directory contents
   - [ ] `file_search()` - Search in file
   - [ ] `file_find()` - Find files by pattern
   - [ ] `file_replace()` - Replace string in file

2. **Implement File Transfer**
   - [ ] `file_upload()` - Upload file to sandbox via Cloud Storage
   - [ ] `file_download()` - Download file from sandbox via Cloud Storage
   - [ ] Handle large files with streaming
   - [ ] Implement size limits (500MB max)
   - [ ] Add progress tracking for large files

3. **File Operation Tests**
   - [ ] Test all file operations
   - [ ] Test large file upload/download (>100MB)
   - [ ] Test file size limits
   - [ ] Test error handling (permissions, not found, etc.)

#### Validation Checkpoint

**Tests to Pass:**
```bash
pytest backend/tests/unit/test_cloudrun_jobs_sandbox.py::TestFileOperations -v
pytest backend/tests/integration/test_cloudrun_jobs_sandbox_real.py::TestFileOperations -v
```

**Success Criteria:**
```python
# File operations must work
await sandbox.file_write("/tmp/test.txt", "content")
result = await sandbox.file_read("/tmp/test.txt")
assert result.data["content"] == "content"

# File upload/download
with open("test.bin", "rb") as f:
    await sandbox.file_upload(f, "/tmp/upload.bin")

downloaded = await sandbox.file_download("/tmp/upload.bin")
assert downloaded.read() == original_content
```

**Rollback**: Still not integrated, safe to revert

---

### Phase 5: Sandbox Protocol Compatibility (Week 5)

**Goal**: Implement remaining methods for full [`Sandbox`](../backend/app/domain/external/sandbox.py) protocol compatibility

#### Tasks

1. **Implement Session Lifecycle Methods**
   - [ ] `create()` - Class method to create new sandbox
   - [ ] `get()` - Class method to retrieve sandbox by ID
   - [ ] `ensure_sandbox()` - Health check and readiness verification
   - [ ] `destroy()` - Cleanup resources and delete jobs

2. **Implement Process Control Methods**
   - [ ] `exec_command()` - Legacy method (wrapper around `exec_command_stateful()`)
   - [ ] `view_shell()` - View shell status (return session info)
   - [ ] `wait_for_process()` - Wait for process completion
   - [ ] `write_to_process()` - Write input to process (not applicable, return error)
   - [ ] `kill_process()` - Terminate process

3. **Implement Browser Methods**
   - [ ] `get_browser()` - Return browser instance (not supported, raise NotImplementedError)
   - [ ] Document limitation: CDP not available in Cloud Run Jobs

4. **Implement Session Management**
   - [ ] `list_sessions()` - List all active sessions
   - [ ] `get_session_info()` - Get session details
   - [ ] `close_session()` - Close and cleanup session
   - [ ] `cleanup_all_sessions()` - Bulk session cleanup

5. **Comprehensive Protocol Tests**
   - [ ] Test all 40+ methods from Sandbox protocol
   - [ ] Verify type signatures match protocol
   - [ ] Test error handling for unsupported methods

#### Validation Checkpoint

**Tests to Pass:**
```bash
# All CloudRunJobsSandbox tests
pytest backend/tests/unit/test_cloudrun_jobs_sandbox.py -v
pytest backend/tests/integration/test_cloudrun_jobs_sandbox_real.py -v -m integration

# Protocol compatibility check
pytest backend/tests/unit/test_sandbox_protocol_compatibility.py -v
```

**Success Criteria:**
- ✅ All Sandbox protocol methods implemented
- ✅ Type checking passes: `mypy backend/app/infrastructure/external/sandbox/cloudrun_jobs_sandbox.py`
- ✅ CloudRunJobsSandbox is drop-in replacement for DockerSandbox (interface-wise)
- ✅ Unsupported methods (browser, CDP) documented and raise appropriate errors

**Rollback**: Still not integrated, safe to revert

---

### Phase 6: Factory Pattern & Feature Flag (Week 6)

**Goal**: Create sandbox factory with feature flag for safe rollout

#### Tasks

1. **Create Sandbox Factory**
   - [ ] Create `backend/app/infrastructure/external/sandbox/factory.py`:
     ```python
     from app.core.config import get_settings
     from app.domain.external.sandbox import Sandbox
     from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
     from app.infrastructure.external.sandbox.cloudrun_jobs_sandbox import CloudRunJobsSandbox
     
     async def get_sandbox() -> Sandbox:
         """
         Get sandbox instance based on configuration.
         
         Uses feature flag USE_CLOUDRUN_JOBS_SANDBOX to control rollout.
         """
         settings = get_settings()
         
         if settings.use_cloudrun_jobs_sandbox:
             return await CloudRunJobsSandbox.create()
         else:
             return await DockerSandbox.create()
     ```

2. **Update Dependency Injection**
   - [ ] Update [`backend/app/interfaces/dependencies.py`](../backend/app/interfaces/dependencies.py:54):
     ```python
     # OLD (line 54):
     # sandbox_cls = DockerSandbox
     
     # NEW:
     from app.infrastructure.external.sandbox.factory import get_sandbox
     
     # In get_agent_service():
     return AgentService(
         llm=llm,
         agent_repository=agent_repository,
         session_repository=session_repository,
         sandbox_factory=get_sandbox,  # Pass factory function
         task_cls=task_cls,
         json_parser=json_parser,
         file_storage=file_storage,
         search_engine=search_engine,
         mcp_repository=mcp_repository,
     )
     ```
   - [ ] Update [`AgentService`](../backend/app/application/services/agent_service.py) to accept `sandbox_factory` instead of `sandbox_cls`

3. **Environment Configuration**
   - [ ] Add to `.env`:
     ```bash
     # Sandbox Configuration
     USE_CLOUDRUN_JOBS_SANDBOX=false  # Feature flag (default: false)
     GCP_PROJECT_ID=your-project-id
     GCP_REGION=us-central1
     SANDBOX_EXECUTOR_IMAGE=gcr.io/your-project/sandbox-executor:latest
     SANDBOX_STATE_BUCKET=your-project-sandbox-sessions
     ```

4. **Integration Tests with Feature Flag**
   - [ ] Test with `USE_CLOUDRUN_JOBS_SANDBOX=false` (should use DockerSandbox)
   - [ ] Test with `USE_CLOUDRUN_JOBS_SANDBOX=true` (should use CloudRunJobsSandbox)
   - [ ] Verify no code changes needed in agent workflows

#### Validation Checkpoint

**Tests to Pass:**
```bash
# With DockerSandbox (default)
USE_CLOUDRUN_JOBS_SANDBOX=false pytest backend/tests/ -v

# With CloudRunJobsSandbox
USE_CLOUDRUN_JOBS_SANDBOX=true pytest backend/tests/ -v -m integration
```

**Success Criteria:**
- ✅ Factory pattern works correctly
- ✅ Feature flag controls sandbox selection
- ✅ No code changes in agent workflows
- ✅ All existing tests pass with DockerSandbox
- ✅ All tests pass with CloudRunJobsSandbox (in GCP environment)

**Rollback**: Set `USE_CLOUDRUN_JOBS_SANDBOX=false` (immediate revert)

---

### Phase 7: Staging Deployment & Validation (Week 7)

**Goal**: Deploy to staging environment and validate with real workloads

#### Tasks

1. **Staging Environment Setup**
   - [ ] Deploy to staging Cloud Run service
   - [ ] Configure environment variables
   - [ ] Verify GCP permissions in staging
   - [ ] Set up monitoring and logging

2. **Gradual Rollout Plan**
   - [ ] **Step 1**: Deploy with `USE_CLOUDRUN_JOBS_SANDBOX=false` (baseline)
   - [ ] **Step 2**: Deploy with flag, but keep at 0% traffic
   - [ ] **Step 3**: Route 1% of sessions to CloudRunJobsSandbox
   - [ ] **Step 4**: Monitor for 24 hours, check metrics
   - [ ] **Step 5**: Increase to 10% if no issues
   - [ ] **Step 6**: Monitor for 48 hours
   - [ ] **Step 7**: Increase to 50% if metrics look good
   - [ ] **Step 8**: Monitor for 72 hours
   - [ ] **Step 9**: Increase to 100% if everything stable

3. **Implement Traffic Splitting**
   - [ ] Add percentage-based routing in factory:
     ```python
     import random
     
     async def get_sandbox() -> Sandbox:
         settings = get_settings()
         
         if not settings.use_cloudrun_jobs_sandbox:
             return await DockerSandbox.create()
         
         # Gradual rollout: use percentage
         rollout_percentage = settings.cloudrun_jobs_rollout_percentage
         if random.random() * 100 < rollout_percentage:
             return await CloudRunJobsSandbox.create()
         else:
             return await DockerSandbox.create()
     ```

4. **Monitoring Setup**
   - [ ] Set up Cloud Monitoring dashboards
   - [ ] Configure alerting for:
     - Job failure rate > 1%
     - Execution latency p99 > 10s
     - Error rate increase
     - Cost anomalies
   - [ ] Set up log aggregation and analysis

5. **E2E Testing in Staging**
   - [ ] Run all E2E test suites
   - [ ] Test agent workflows end-to-end
   - [ ] Test file upload/download with real files
   - [ ] Test background processes
   - [ ] Load testing with concurrent executions

#### Validation Checkpoint

**Tests to Pass:**
```bash
# E2E tests in staging
pytest backend/tests/e2e/ -v --env=staging

# Load testing
python scripts/load_test_sandbox.py --concurrent=10 --duration=300
```

**Metrics to Monitor:**
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Job success rate | >99.5% | <99% |
| Execution latency p50 | <3s | >5s |
| Execution latency p99 | <10s | >15s |
| Error rate | <0.5% | >1% |
| Cost per 1000 executions | <$0.50 | >$1.00 |

**Success Criteria:**
- ✅ All E2E tests pass in staging
- ✅ No errors in logs during 24h monitoring
- ✅ Latency within acceptable range
- ✅ Cost projections under budget
- ✅ Zero critical issues reported

**Rollback**: Set `USE_CLOUDRUN_JOBS_SANDBOX=false` or reduce `cloudrun_jobs_rollout_percentage=0`

---

### Phase 8: Production Deployment (Week 8)

**Goal**: Roll out to production with careful monitoring

#### Tasks

1. **Pre-Production Checklist**
   - [ ] All staging tests passed
   - [ ] Monitoring dashboards configured
   - [ ] Alerting rules validated
   - [ ] Runbook documentation complete
   - [ ] Rollback procedure tested
   - [ ] On-call engineer assigned

2. **Production Deployment**
   - [ ] Deploy to production with `USE_CLOUDRUN_JOBS_SANDBOX=false` (safety)
   - [ ] Verify deployment successful
   - [ ] Enable feature flag: `USE_CLOUDRUN_JOBS_SANDBOX=true`
   - [ ] Start rollout at 1%: `CLOUDRUN_JOBS_ROLLOUT_PERCENTAGE=1`

3. **Gradual Production Rollout**
   - [ ] **Day 1**: 1% traffic, monitor 24h
   - [ ] **Day 2**: 10% traffic, monitor 48h
   - [ ] **Day 4**: 25% traffic, monitor 48h
   - [ ] **Day 6**: 50% traffic, monitor 72h
   - [ ] **Day 9**: 75% traffic, monitor 48h
   - [ ] **Day 11**: 100% traffic

4. **Post-Deployment Validation**
   - [ ] Verify metrics match staging performance
   - [ ] Check user feedback/support tickets
   - [ ] Analyze cost vs. projections
   - [ ] Document any issues and resolutions

5. **Cleanup Phase** (After 2 weeks stable)
   - [ ] Remove DockerSandbox dependency (optional)
   - [ ] Update documentation
   - [ ] Archive old test cases
   - [ ] Remove feature flag code

#### Validation Checkpoint

**Continuous Monitoring:**
- Monitor same metrics as staging
- Watch for user complaints/support tickets
- Track cost daily vs. budget

**Success Criteria:**
- ✅ 100% rollout achieved
- ✅ Metrics stable for 2 weeks
- ✅ No critical incidents
- ✅ User satisfaction maintained
- ✅ Cost within budget

**Rollback**: Set `CLOUDRUN_JOBS_ROLLOUT_PERCENTAGE=0` (immediate revert to DockerSandbox)

---

## Testing Strategy

### Test Pyramid

```
        E2E Tests (10 tests)
       /                    \
      /    Integration Tests   \
     /        (50 tests)         \
    /                              \
   /       Unit Tests (200 tests)   \
  /____________________________________\
```

### Unit Tests (200+ tests)

**Coverage Target**: 90%+

**Test Files:**
- `backend/tests/unit/test_cloudrun_jobs_sandbox.py`
- `backend/tests/unit/test_cloudrun_job_manager.py`
- `backend/tests/unit/test_session_state_manager.py`
- `backend/tests/unit/test_sandbox_factory.py`

**Test Categories:**
1. **Initialization Tests** (10 tests)
   - Configuration parsing
   - Client initialization
   - Error handling for missing config

2. **Job Management Tests** (30 tests)
   - Job creation
   - Job execution
   - Status polling
   - Job cleanup
   - Error handling
   - Retry logic

3. **State Management Tests** (40 tests)
   - State loading
   - State saving
   - State versioning
   - State consistency
   - Error handling
   - Caching

4. **Command Execution Tests** (50 tests)
   - Simple commands
   - CWD preservation
   - ENV preservation
   - Background processes
   - Timeout handling
   - Error handling

5. **File Operations Tests** (40 tests)
   - Read/Write/Delete
   - Upload/Download
   - Search/Find/Replace
   - Large files
   - Error handling

6. **Protocol Compatibility Tests** (30 tests)
   - All Sandbox methods
   - Type checking
   - Error handling

### Integration Tests (50+ tests)

**Environment**: Real GCP (marked with `@pytest.mark.integration`)

**Test Files:**
- `backend/tests/integration/test_cloudrun_jobs_sandbox_real.py`
- `backend/tests/integration/test_sandbox_migration.py`

**Test Categories:**
1. **Real Job Execution** (20 tests)
   - Actual Cloud Run Jobs
   - Real state persistence
   - Real file operations
   - Performance benchmarks

2. **Migration Testing** (15 tests)
   - Factory pattern
   - Feature flag toggling
   - Parallel execution
   - Session migration

3. **Error Scenarios** (15 tests)
   - Network failures
   - Permission errors
   - Resource exhaustion
   - Recovery mechanisms

### E2E Tests (10+ tests)

**Environment**: Full stack with real agents

**Test Files:**
- `backend/tests/e2e/test_agent_with_cloudrun_sandbox.py`

**Test Scenarios:**
1. Complete agent workflow with CloudRunJobsSandbox
2. File upload/download in agent context
3. Background process management in workflow
4. Session lifecycle with multiple agents
5. Error recovery in production-like scenarios

### Performance Tests

**Benchmarks to Track:**

| Operation | DockerSandbox | CloudRunJobsSandbox | Acceptance |
|-----------|---------------|---------------------|------------|
| Cold Start | N/A | 3-7s | <10s |
| Warm Execution | 0.1-0.5s | 0.5-2s | <3s |
| File Upload (10MB) | 1-2s | 2-4s | <5s |
| File Download (10MB) | 1-2s | 2-4s | <5s |
| Background Process Start | 0.5-1s | 1-2s | <3s |

### Load Tests

**Test Scenarios:**
```bash
# Concurrent executions
python scripts/load_test.py --concurrent=20 --duration=300

# Session stress test
python scripts/session_stress_test.py --sessions=100 --commands=50

# File operation stress
python scripts/file_stress_test.py --files=100 --size=10MB
```

---

## Rollback Procedures

### Immediate Rollback (< 1 minute)

**Trigger**: Critical production issue detected

**Procedure:**
1. Set environment variable:
   ```bash
   gcloud run services update manus-backend \
     --set-env-vars USE_CLOUDRUN_JOBS_SANDBOX=false
   ```
2. Verify rollback in logs
3. Monitor metrics for recovery
4. Investigate root cause

### Gradual Rollback (Reduce Traffic)

**Trigger**: Non-critical issues or performance degradation

**Procedure:**
1. Reduce rollout percentage:
   ```bash
   gcloud run services update manus-backend \
     --set-env-vars CLOUDRUN_JOBS_ROLLOUT_PERCENTAGE=0
   ```
2. Monitor for 30 minutes
3. Analyze issues
4. Fix and re-deploy

### Complete Rollback (Remove Feature)

**Trigger**: CloudRunJobsSandbox fundamentally flawed

**Procedure:**
1. Set `USE_CLOUDRUN_JOBS_SANDBOX=false`
2. Deploy updated code removing factory pattern
3. Restore direct `DockerSandbox` usage in dependencies
4. Remove CloudRunJobsSandbox code
5. Document lessons learned

### Rollback Testing

**Before Each Phase:**
- Practice rollback in staging
- Time the rollback procedure
- Verify system recovery
- Document any issues

---

## Monitoring & Validation

### Key Metrics to Track

#### Success Metrics

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Job Success Rate | Cloud Logging | <99% |
| Execution Latency (p50) | Cloud Monitoring | >5s |
| Execution Latency (p99) | Cloud Monitoring | >15s |
| Error Rate | Application Logs | >1% |
| State Consistency | Custom Metric | <100% |

#### Cost Metrics

| Metric | Source | Budget |
|--------|--------|--------|
| Cloud Run Jobs vCPU | GCP Billing | $100/month |
| Cloud Run Jobs Memory | GCP Billing | $20/month |
| Cloud Storage | GCP Billing | $5/month |
| Network Egress | GCP Billing | $10/month |
| **Total** | | **$135/month** |

#### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cold Start Time | <7s | Cloud Monitoring |
| Warm Execution Time | <2s | Cloud Monitoring |
| State Load Time | <200ms | Application Metrics |
| State Save Time | <300ms | Application Metrics |

### Monitoring Dashboards

**Cloud Monitoring Dashboard:**
```json
{
  "displayName": "CloudRun Jobs Sandbox",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Job Success Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_job\" AND metric.type=\"run.googleapis.com/job/completed_executions\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
```

### Alerting Rules

**Critical Alerts:**
1. **Job Failure Rate > 1%**
   - Notify: On-call engineer
   - Action: Immediate investigation

2. **Execution Latency p99 > 15s**
   - Notify: Engineering team
   - Action: Performance analysis

3. **Cost Anomaly (>2x expected)**
   - Notify: Engineering + Finance
   - Action: Check for quota/billing issues

**Warning Alerts:**
1. **Job Success Rate < 99.5%**
2. **State Save Failures**
3. **GCP Permission Errors**

### Logging Strategy

**Structured Logging:**
```python
import logging
import json

logger = logging.getLogger("cloudrun_jobs_sandbox")

logger.info(json.dumps({
    "event": "job_execution_started",
    "execution_id": execution_id,
    "session_id": session_id,
    "command": command,
    "timestamp": datetime.utcnow().isoformat()
}))
```

**Log Queries:**
```
# Failed job executions
resource.type="cloud_run_job"
severity>=ERROR
jsonPayload.event="job_execution_failed"

# High latency executions
resource.type="cloud_run_job"
jsonPayload.event="job_execution_completed"
jsonPayload.duration_seconds>10

# State management errors
resource.type="cloud_run_service"
jsonPayload.component="session_state_manager"
severity>=ERROR
```

---

## Migration Checklist

### Pre-Migration (Week 0)

- [ ] GCP project configured
- [ ] IAM permissions validated
- [ ] Cloud Storage bucket created
- [ ] Configuration added to codebase
- [ ] Baseline metrics documented
- [ ] All existing tests pass

### Phase 1 Completion (Week 1-2)

- [ ] Executor container built and deployed
- [ ] CloudRunJobsSandbox class structure created
- [ ] Unit tests passing
- [ ] No regression in existing tests

### Phase 2 Completion (Week 2-3)

- [ ] Job management implemented
- [ ] State management implemented
- [ ] `exec_command_stateful()` working
- [ ] Integration tests passing
- [ ] Performance benchmarks acceptable

### Phase 3 Completion (Week 3-4)

- [ ] Background process management implemented
- [ ] Process tracking working
- [ ] Kill and log retrieval working
- [ ] Background process tests passing

### Phase 4 Completion (Week 4-5)

- [ ] All file operations implemented
- [ ] File upload/download working
- [ ] Large file handling tested
- [ ] File operation tests passing

### Phase 5 Completion (Week 5)

- [ ] All Sandbox protocol methods implemented
- [ ] Protocol compatibility validated
- [ ] Type checking passing
- [ ] Comprehensive test suite passing

### Phase 6 Completion (Week 6)

- [ ] Factory pattern implemented
- [ ] Feature flag configured
- [ ] Dependency injection updated
- [ ] Tests passing with both implementations

### Phase 7 Completion (Week 7)

- [ ] Deployed to staging
- [ ] Gradual rollout completed in staging
- [ ] Monitoring validated
- [ ] E2E tests passing
- [ ] Performance acceptable

### Phase 8 Completion (Week 8)

- [ ] Deployed to production
- [ ] Gradual rollout completed in production
- [ ] Metrics stable for 2 weeks
- [ ] No critical incidents
- [ ] Documentation updated

---

## Appendix

### A. Configuration Reference

**Environment Variables:**
```bash
# Feature Flag
USE_CLOUDRUN_JOBS_SANDBOX=false

# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Executor Configuration
SANDBOX_EXECUTOR_IMAGE=gcr.io/your-project/sandbox-executor:latest
SANDBOX_STATE_BUCKET=your-project-sandbox-sessions
SANDBOX_JOB_TIMEOUT=120
SANDBOX_JOB_MEMORY=512Mi
SANDBOX_JOB_CPU=1

# Gradual Rollout
CLOUDRUN_JOBS_ROLLOUT_PERCENTAGE=0
```

### B. Useful Commands

**Build Executor:**
```bash
cd backend/sandbox-executor
./build.sh
```

**Run Tests:**
```bash
# Unit tests
pytest backend/tests/unit/test_cloudrun_jobs_sandbox.py -v

# Integration tests (requires GCP)
pytest backend/tests/integration/test_cloudrun_jobs_sandbox_real.py -v -m integration

# All tests
pytest backend/tests/ -v
```

**Deploy to Staging:**
```bash
gcloud run deploy manus-backend-staging \
  --image gcr.io/your-project/manus-backend:latest \
  --region us-central1 \
  --set-env-vars USE_CLOUDRUN_JOBS_SANDBOX=true,GCP_PROJECT_ID=your-project
```

**Monitor Logs:**
```bash
# Job execution logs
gcloud logging read "resource.type=cloud_run_job" --limit 50 --format json

# Application logs
gcloud logging read "resource.type=cloud_run_service AND jsonPayload.component=cloudrun_jobs_sandbox" --limit 50
```

### C. Troubleshooting Guide

**Issue**: Job creation fails with permission denied

**Solution**:
1. Check service account permissions
2. Verify IAM roles assigned
3. Check Cloud Run API enabled

**Issue**: State not persisting between executions

**Solution**:
1. Check Cloud Storage bucket permissions
2. Verify state saving logic in executor
3. Check for network issues

**Issue**: High latency (>10s)

**Solution**:
1. Check cold start time
2. Optimize executor image size
3. Consider pre-warming strategies

---

## Conclusion

This implementation plan provides a **safe, incremental approach** to migrating from DockerSandbox to CloudRunJobsSandbox:

**Key Safety Mechanisms:**
1. ✅ Never modify existing DockerSandbox code
2. ✅ Implement CloudRunJobsSandbox in isolation
3. ✅ Use feature flags for gradual rollout
4. ✅ Comprehensive testing at every phase
5. ✅ Rollback capability at all times
6. ✅ Continuous monitoring and validation

**Timeline**: 6-8 weeks with validation checkpoints

**Risk**: Low (with proper execution of this plan)

**Confidence**: High (extensive testing and gradual rollout)

**Next Steps**:
1. Review and approve this plan
2. Begin Phase 0: Prerequisites setup
3. Proceed phase-by-phase with validation
4. Monitor and adjust as needed

---

**Document Status**: Ready for Review  
**Last Updated**: 2025-12-28  
**Author**: Architect Mode