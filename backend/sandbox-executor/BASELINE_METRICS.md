# Phase 0 Baseline Metrics Documentation

**Date**: 2025-12-28  
**System**: Manus AI Backend (DockerSandbox)  
**Purpose**: Establish baseline metrics before Cloud Run Jobs Sandbox migration

---

## Health Check Metrics

### Current Endpoints

1. **`/health`** - Basic health check
   - Returns: `200 OK` if application is running
   - Response time: < 100ms
   - Used by: Load balancers, uptime monitors
   
2. **`/ready`** - Readiness check with dependency validation
   - Checks: MongoDB, Redis, Stripe (if configured)
   - Returns: `200 OK` (allows degraded mode)
   - Response time: < 500ms with lazy initialization
   - Status modes: `ready`, `degraded`
   
3. **`/live`** - Liveness check
   - Returns: `200 OK` if process is responsive
   - Response time: < 50ms
   - Used by: Kubernetes liveness probes

### Current Response Times (Baseline)

| Endpoint | Target | Typical | Max Acceptable |
|----------|--------|---------|----------------|
| `/health` | < 100ms | ~50ms | 200ms |
| `/ready` | < 500ms | ~300ms | 1000ms |
| `/live` | < 50ms | ~20ms | 100ms |

---

## Sandbox Protocol Interface

### Current Implementation: DockerSandbox

The Sandbox protocol defines 40+ methods across several categories:

#### Core Command Execution
- `exec_command()` - Legacy command execution
- `exec_command_stateful()` - **NEW** Stateful execution with CWD/ENV preservation
- `ensure_sandbox()` - Readiness verification

#### File Operations (16 methods)
- `file_read()`, `file_write()`, `file_delete()`
- `file_exists()`, `file_list()`, `file_find()`
- `file_search()`, `file_replace()`
- `file_upload()`, `file_download()`

#### Process Management
- `wait_for_process()`, `write_to_process()`, `kill_process()`
- `view_shell()` - Shell status viewing

#### Background Process Management (NEW Stateful Features)
- `list_background_processes()` - List all background processes
- `kill_background_process()` - Kill by PID/session/pattern
- `get_background_logs()` - Retrieve process logs

#### Browser Integration
- `get_browser()` - Browser instance for web automation

#### Lifecycle Management
- `create()` - Create new sandbox instance
- `get()` - Retrieve sandbox by ID
- `destroy()` - Cleanup resources

---

## DockerSandbox Performance Baseline

### Command Execution Performance

Based on typical Docker container operations:

| Operation | Target | Notes |
|-----------|--------|-------|
| Cold Start | N/A | Container reuse eliminates cold starts |
| Warm Execution | 0.1-0.5s | Docker exec overhead |
| File Upload (10MB) | 1-2s | Docker cp performance |
| File Download (10MB) | 1-2s | Docker cp performance |
| Background Process Start | 0.5-1s | Process fork in container |

### Error Rates

Current production error rates (expected baseline):
- **Success Rate**: >99.5%
- **Timeout Rate**: <0.1%
- **Network Error Rate**: <0.1%
- **Permission Error Rate**: <0.1%

---

## Test Coverage Baseline

### Existing Test Files

Need to inventory existing sandbox tests:
- `backend/tests/unit/test_docker_sandbox.py` (if exists)
- `backend/tests/integration/test_sandbox_integration.py` (if exists)

### Expected Test Results

All existing DockerSandbox tests must pass with:
- **0 failures**
- **0 errors**
- **Coverage**: >80% for sandbox code

Command to run:
```bash
pytest backend/tests/unit/test_docker_sandbox.py -v --durations=10
pytest backend/tests/integration/test_sandbox_integration.py -v
```

---

## Cloud Run Jobs Sandbox Acceptance Criteria

### Performance Targets

Compared to DockerSandbox baseline:

| Metric | DockerSandbox | CloudRunJobsSandbox Target | Acceptable |
|--------|---------------|---------------------------|------------|
| Cold Start | N/A | 3-7s | <10s |
| Warm Execution | 0.1-0.5s | 0.5-2s | <3s |
| File Upload (10MB) | 1-2s | 2-4s | <5s |
| File Download (10MB) | 1-2s | 2-4s | <5s |
| Background Process Start | 0.5-1s | 1-2s | <3s |
| Success Rate | >99.5% | >99.5% | >99% |

### Functional Parity Requirements

CloudRunJobsSandbox MUST:
- ✅ Implement all 40+ Sandbox protocol methods
- ✅ Pass all existing DockerSandbox tests
- ✅ Preserve CWD between commands in same session
- ✅ Preserve ENV between commands in same session
- ✅ Support background processes with PID tracking
- ✅ Support file upload/download with streaming
- ✅ Handle files up to 500MB
- ✅ Provide proper error handling and logging

### Known Limitations

CloudRunJobsSandbox will NOT support:
- ❌ Browser/CDP access (Cloud Run Jobs has no display)
- ❌ VNC access (no virtual display)
- ❌ Real-time interactive TTY (async batch execution)

These limitations are documented and will raise `NotImplementedError`.

---

## Monitoring Metrics to Track

### Key Metrics During Migration

1. **Success Rate**
   - Source: Cloud Logging
   - Alert: <99%
   - Query: `resource.type="cloud_run_job" AND jsonPayload.event="job_execution_completed"`

2. **Execution Latency**
   - p50: <3s
   - p99: <10s
   - Alert: p99 >15s

3. **Error Rate**
   - Target: <0.5%
   - Alert: >1%

4. **Cost**
   - Budget: $135/month
   - Alert: >$200/month

5. **State Consistency**
   - Target: 100%
   - Alert: Any state loss

### Logging Strategy

Structured JSON logging with fields:
- `event`: Event type (job_execution_started, job_execution_completed, etc.)
- `execution_id`: Unique execution identifier
- `session_id`: Session identifier
- `command`: Command executed
- `duration_seconds`: Execution duration
- `exit_code`: Command exit code
- `timestamp`: ISO 8601 timestamp

---

## GCP Resource Configuration

### Cloud Storage Bucket

- **Name**: `manus-sandbox-state`
- **Location**: `us-central1`
- **Storage Class**: `STANDARD`
- **Lifecycle**: Delete sessions older than 7 days
- **Purpose**: Store session state and execution results

### Sandbox Executor Container

- **Image**: `us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/sandbox-executor:v0.1.0`
- **Base**: Python 3.11-slim
- **Size**: ~1.2 GB (with system dependencies)
- **Build Time**: ~3 minutes
- **Status**: ✅ Successfully built and pushed

### Cloud Run Jobs Configuration

- **Project**: `gen-lang-client-0415541083`
- **Region**: `us-central1`
- **Memory**: `512Mi` (default)
- **CPU**: `1` (default)
- **Timeout**: `120s` (default)
- **Concurrency**: Multiple jobs can run simultaneously

---

## Phase 0 Validation Checklist

### Prerequisites Completed

- [x] GCS bucket created with lifecycle policy
- [x] Sandbox executor container built and pushed
- [x] Baseline metrics documented
- [ ] Test harness created
- [ ] GCP permissions validated
- [ ] Cloud Run Jobs API enabled
- [ ] Test job creation validated

### Next Steps

1. Create test harness in `backend/tests/sandbox/`
2. Validate GCP IAM permissions
3. Confirm Cloud Run Jobs API is enabled
4. Test creating and deleting a simple Cloud Run Job
5. Generate Phase 0 completion report

---

## References

- Implementation Plan: [`plans/CLOUDRUN_JOBS_SANDBOX_IMPLEMENTATION_PLAN.md`](../../plans/CLOUDRUN_JOBS_SANDBOX_IMPLEMENTATION_PLAN.md)
- Sandbox Protocol: [`backend/app/domain/external/sandbox.py`](../app/domain/external/sandbox.py)
- Health Routes: [`backend/app/interfaces/api/health_routes.py`](../app/interfaces/api/health_routes.py)
- GCP Permissions: [`GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md`](../../GCP_CLOUDRUN_JOBS_PERMISSIONS_SETUP.md)

---

**Document Status**: Baseline Established  
**Last Updated**: 2025-12-28  
**Next Review**: After Phase 1 completion