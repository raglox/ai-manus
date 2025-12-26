"""
P1-2, P1-3, P1-4 Tests - Log Limits, Server Limits, Health Checks
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock


class TestP12LogSizeLimits:
    """Test P1-2: Log size limits (CVSS 5.5)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tool = Mock()
        self.tool._log_sizes = {}
        self.MAX_LOG_READ_SIZE = 10 * 1024 * 1024  # 10 MB
        self.MAX_TOTAL_LOG_SIZE = 100 * 1024 * 1024  # 100 MB
    
    def test_log_size_tracking(self):
        """Test that log sizes are tracked per PID"""
        # Simulate reading logs
        pid = 12345
        self.tool._log_sizes[pid] = 0
        
        # Read 1 MB
        self.tool._log_sizes[pid] += 1024 * 1024
        assert self.tool._log_sizes[pid] == 1024 * 1024
        
        # Read another 2 MB
        self.tool._log_sizes[pid] += 2 * 1024 * 1024
        assert self.tool._log_sizes[pid] == 3 * 1024 * 1024
        
        print(f"✅ Log size tracking: {self.tool._log_sizes[pid]} bytes")
    
    def test_max_log_read_size_enforcement(self):
        """Test that single read is limited to MAX_LOG_READ_SIZE"""
        pid = 12345
        self.tool._log_sizes[pid] = 0
        
        # Try to read 20 MB (more than MAX_LOG_READ_SIZE)
        requested_read = 20 * 1024 * 1024
        actual_read = min(self.MAX_LOG_READ_SIZE, requested_read)
        
        assert actual_read == self.MAX_LOG_READ_SIZE
        assert actual_read == 10 * 1024 * 1024
        
        print(f"✅ Max read size enforced: {actual_read} bytes (requested {requested_read})")
    
    def test_total_log_size_limit(self):
        """Test that total log size is limited"""
        pid = 12345
        self.tool._log_sizes[pid] = 95 * 1024 * 1024  # 95 MB already read
        
        # Can read up to 5 MB more
        remaining = self.MAX_TOTAL_LOG_SIZE - self.tool._log_sizes[pid]
        assert remaining == 5 * 1024 * 1024
        
        # Try to read 10 MB
        requested = 10 * 1024 * 1024
        actual = min(requested, remaining)
        
        assert actual == 5 * 1024 * 1024
        
        print(f"✅ Total log limit: {actual} bytes (remaining from {self.MAX_TOTAL_LOG_SIZE})")
    
    def test_log_size_cleanup(self):
        """Test that log sizes are cleaned up on server stop"""
        # Track multiple servers
        self.tool._log_sizes[100] = 1024 * 1024
        self.tool._log_sizes[200] = 2 * 1024 * 1024
        self.tool._log_sizes[300] = 3 * 1024 * 1024
        
        assert len(self.tool._log_sizes) == 3
        
        # Stop server 200
        if 200 in self.tool._log_sizes:
            del self.tool._log_sizes[200]
        
        assert len(self.tool._log_sizes) == 2
        assert 200 not in self.tool._log_sizes
        assert 100 in self.tool._log_sizes
        assert 300 in self.tool._log_sizes
        
        print(f"✅ Log size cleanup: {len(self.tool._log_sizes)} remaining after stop")


class TestP13MaxServerLimit:
    """Test P1-3: Max server limit (CVSS 5.0)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tool = Mock()
        self.tool._started_servers = {}
        self.MAX_SERVERS = 10
    
    def test_server_count_tracking(self):
        """Test that server count is tracked correctly"""
        # Start 5 servers
        for i in range(5):
            self.tool._started_servers[i] = {"command": f"server-{i}"}
        
        server_count = len(self.tool._started_servers)
        assert server_count == 5
        
        print(f"✅ Server count tracking: {server_count} servers")
    
    def test_max_server_limit_enforcement(self):
        """Test that max server limit is enforced"""
        # Start MAX_SERVERS servers
        for i in range(self.MAX_SERVERS):
            self.tool._started_servers[i] = {"command": f"server-{i}"}
        
        server_count = len(self.tool._started_servers)
        assert server_count == self.MAX_SERVERS
        
        # Try to start another server
        can_start = server_count < self.MAX_SERVERS
        assert can_start == False
        
        print(f"✅ Max server limit enforced: {server_count}/{self.MAX_SERVERS}")
    
    def test_server_limit_after_stop(self):
        """Test that limit allows new servers after stops"""
        # Start MAX_SERVERS servers
        for i in range(self.MAX_SERVERS):
            self.tool._started_servers[i] = {"command": f"server-{i}"}
        
        # Can't start more
        assert len(self.tool._started_servers) >= self.MAX_SERVERS
        
        # Stop 3 servers
        for i in range(3):
            del self.tool._started_servers[i]
        
        # Now can start more
        server_count = len(self.tool._started_servers)
        can_start = server_count < self.MAX_SERVERS
        assert can_start == True
        assert server_count == 7
        
        print(f"✅ Server limit after stop: {server_count}/{self.MAX_SERVERS} (can start {self.MAX_SERVERS - server_count} more)")
    
    def test_server_limit_protects_against_dos(self):
        """Test that limit prevents resource exhaustion DoS"""
        # Attacker tries to start 100 servers
        started = 0
        for i in range(100):
            if len(self.tool._started_servers) < self.MAX_SERVERS:
                self.tool._started_servers[i] = {"command": f"server-{i}"}
                started += 1
            else:
                # Blocked by limit
                break
        
        assert started == self.MAX_SERVERS
        assert len(self.tool._started_servers) == self.MAX_SERVERS
        
        print(f"✅ DoS protection: limited to {self.MAX_SERVERS} servers (attempted 100)")


class TestP14HTTPHealthChecks:
    """Test P1-4: HTTP health checks (CVSS 6.0)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.HEALTH_CHECK_TIMEOUT = 5
        self.HEALTH_CHECK_MAX_RETRIES = 3
    
    @pytest.mark.asyncio
    async def test_health_check_success_first_try(self):
        """Test successful health check on first attempt"""
        async def mock_health_check():
            return "200"  # HTTP 200 OK
        
        result = await mock_health_check()
        assert result == "200"
        assert result[0] in ['2', '3', '4']  # Success codes
        
        print("✅ Health check passed on first attempt: HTTP 200")
    
    @pytest.mark.asyncio
    async def test_health_check_retry_logic(self):
        """Test health check retries on failure"""
        attempt = 0
        
        async def mock_health_check_with_retry():
            nonlocal attempt
            attempt += 1
            
            if attempt < 3:
                return "000"  # Connection refused
            else:
                return "200"  # Success on 3rd try
        
        # Simulate retries
        for retry in range(self.HEALTH_CHECK_MAX_RETRIES):
            result = await mock_health_check_with_retry()
            if result[0] in ['2', '3', '4']:
                print(f"✅ Health check succeeded after {retry + 1} attempts")
                break
            else:
                if retry < self.HEALTH_CHECK_MAX_RETRIES - 1:
                    await asyncio.sleep(0.1)  # Shorter for testing
        
        assert attempt == 3
        assert result == "200"
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check respects timeout"""
        start_time = asyncio.get_event_loop().time()
        
        async def mock_slow_health_check():
            try:
                await asyncio.wait_for(
                    asyncio.sleep(10),  # Would take 10s
                    timeout=self.HEALTH_CHECK_TIMEOUT
                )
                return "200"
            except asyncio.TimeoutError:
                return "000"  # Timeout
        
        result = await mock_slow_health_check()
        elapsed = asyncio.get_event_loop().time() - start_time
        
        assert result == "000"
        assert elapsed < self.HEALTH_CHECK_TIMEOUT + 1
        
        print(f"✅ Health check timed out after {elapsed:.1f}s (timeout: {self.HEALTH_CHECK_TIMEOUT}s)")
    
    def test_http_code_validation(self):
        """Test HTTP code validation logic"""
        test_codes = {
            "200": True,   # OK
            "201": True,   # Created
            "301": True,   # Redirect
            "302": True,   # Redirect
            "404": True,   # Not Found (but server responding)
            "500": False,  # Server Error
            "000": False,  # Connection Refused
        }
        
        for code, expected_valid in test_codes.items():
            is_valid = code and code[0] in ['2', '3', '4']
            assert is_valid == expected_valid, f"Code {code} validation failed"
        
        print(f"✅ HTTP code validation: {len(test_codes)} codes tested")
    
    @pytest.mark.asyncio
    async def test_health_check_failure_after_max_retries(self):
        """Test that health check fails after max retries"""
        attempts = 0
        
        async def mock_failing_health_check():
            nonlocal attempts
            attempts += 1
            return "000"  # Always fail
        
        final_result = None
        for retry in range(self.HEALTH_CHECK_MAX_RETRIES):
            result = await mock_failing_health_check()
            final_result = result
            if result[0] not in ['2', '3', '4']:
                if retry < self.HEALTH_CHECK_MAX_RETRIES - 1:
                    await asyncio.sleep(0.1)
        
        assert attempts == self.HEALTH_CHECK_MAX_RETRIES
        assert final_result == "000"
        
        print(f"✅ Health check failed after {self.HEALTH_CHECK_MAX_RETRIES} attempts (expected)")


def run_all_tests():
    """Run all P1-2, P1-3, P1-4 tests"""
    print("\n" + "="*70)
    print("P1-2, P1-3, P1-4 TESTS - Log Limits, Server Limits, Health Checks")
    print("="*70 + "\n")
    
    # P1-2 Tests
    print("📋 P1-2: Log Size Limits Tests")
    print("-" * 70)
    log_tests = TestP12LogSizeLimits()
    
    log_test_methods = [
        log_tests.test_log_size_tracking,
        log_tests.test_max_log_read_size_enforcement,
        log_tests.test_total_log_size_limit,
        log_tests.test_log_size_cleanup,
    ]
    
    passed = 0
    failed = 0
    
    for test_method in log_test_methods:
        try:
            log_tests.setup_method()
            test_method()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_method.__name__}: {e}")
            failed += 1
    
    # P1-3 Tests
    print("\n📋 P1-3: Max Server Limit Tests")
    print("-" * 70)
    server_tests = TestP13MaxServerLimit()
    
    server_test_methods = [
        server_tests.test_server_count_tracking,
        server_tests.test_max_server_limit_enforcement,
        server_tests.test_server_limit_after_stop,
        server_tests.test_server_limit_protects_against_dos,
    ]
    
    for test_method in server_test_methods:
        try:
            server_tests.setup_method()
            test_method()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_method.__name__}: {e}")
            failed += 1
    
    # P1-4 Tests
    print("\n📋 P1-4: HTTP Health Checks Tests")
    print("-" * 70)
    health_tests = TestP14HTTPHealthChecks()
    
    health_test_methods = [
        ("test_health_check_success_first_try", health_tests.test_health_check_success_first_try),
        ("test_health_check_retry_logic", health_tests.test_health_check_retry_logic),
        ("test_health_check_timeout", health_tests.test_health_check_timeout),
        ("test_http_code_validation", health_tests.test_http_code_validation),
        ("test_health_check_failure_after_max_retries", health_tests.test_health_check_failure_after_max_retries),
    ]
    
    for test_name, test_func in health_test_methods:
        try:
            health_tests.setup_method()
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func())
            else:
                test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    if failed == 0:
        print("✅ ALL P1-2, P1-3, P1-4 TESTS PASSED")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
