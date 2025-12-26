"""
Unit tests for webdev.py to achieve >90% coverage
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domain.services.tools.webdev import (
    WebDevTool,
    ALLOWED_BINARIES,
    MAX_LOG_READ_SIZE,
    MAX_TOTAL_LOG_SIZE,
    MAX_SERVERS_PER_TOOL
)


class TestWebDevToolInit:
    """Test WebDevTool initialization"""
    
    def test_init(self):
        """Test tool initialization"""
        sandbox = Mock()
        tool = WebDevTool(sandbox)
        
        assert tool.sandbox == sandbox
        assert tool._started_servers == {}
        assert hasattr(tool, '_server_lock')
        assert tool._log_sizes == {}
        print("✅ WebDevTool initialization test passed")


class TestCommandValidation:
    """Test command validation"""
    
    def setup_method(self):
        """Setup"""
        self.sandbox = Mock()
        self.tool = WebDevTool(self.sandbox)
    
    def test_empty_command(self):
        """Test empty command rejection"""
        with pytest.raises(ValueError) as exc:
            self.tool._validate_command("")
        assert "empty" in str(exc.value).lower()
        print("✅ Empty command rejected")
    
    def test_whitespace_command(self):
        """Test whitespace-only command rejection"""
        with pytest.raises(ValueError) as exc:
            self.tool._validate_command("   \t\n  ")
        assert "empty" in str(exc.value).lower()
        print("✅ Whitespace command rejected")
    
    def test_dangerous_chars(self):
        """Test dangerous character detection"""
        dangerous_commands = [
            "python3 -m http.server; rm -rf /",
            "node server.js | tee output",
            "npm run dev && malicious",
        ]
        
        for cmd in dangerous_commands:
            with pytest.raises(ValueError):
                self.tool._validate_command(cmd)
        print(f"✅ {len(dangerous_commands)} dangerous commands blocked")
    
    def test_forbidden_args(self):
        """Test forbidden arguments"""
        forbidden_commands = [
            "python3 -c 'print(1)'",
            "node --eval 'console.log(1)'",
            "python3 --interactive",
        ]
        
        for cmd in forbidden_commands:
            with pytest.raises(ValueError):
                self.tool._validate_command(cmd)
        print(f"✅ {len(forbidden_commands)} forbidden arguments blocked")
    
    def test_path_in_binary(self):
        """Test path detection in binary"""
        path_commands = [
            "/usr/bin/python3 server.py",
            "./node server.js",
            "../python3 -m http.server",
        ]
        
        for cmd in path_commands:
            with pytest.raises(ValueError):
                self.tool._validate_command(cmd)
        print(f"✅ {len(path_commands)} path commands blocked")
    
    def test_valid_commands(self):
        """Test valid commands pass"""
        valid_commands = [
            "python3 -m http.server 8080",
            "npm run dev",
            "node server.js",
            "flask run --port 5000",
        ]
        
        for cmd in valid_commands:
            self.tool._validate_command(cmd)  # Should not raise
        print(f"✅ {len(valid_commands)} valid commands accepted")


class TestPIDValidation:
    """Test PID validation"""
    
    def setup_method(self):
        """Setup"""
        self.sandbox = Mock()
        self.tool = WebDevTool(self.sandbox)
    
    def test_validate_pid_valid(self):
        """Test valid PID passes"""
        self.tool._validate_pid(12345)
        self.tool._validate_pid(1)
        print("✅ Valid PIDs accepted")
    
    def test_validate_pid_none(self):
        """Test None PID rejected"""
        with pytest.raises(ValueError) as exc:
            self.tool._validate_pid(None)
        assert "none" in str(exc.value).lower()
        print("✅ None PID rejected")
    
    def test_validate_pid_non_integer(self):
        """Test non-integer PID rejected"""
        with pytest.raises(ValueError):
            self.tool._validate_pid("12345")
        print("✅ Non-integer PID rejected")
    
    def test_validate_pid_negative(self):
        """Test negative PID rejected"""
        with pytest.raises(ValueError):
            self.tool._validate_pid(-1)
        print("✅ Negative PID rejected")
    
    def test_validate_pid_zero(self):
        """Test zero PID rejected"""
        with pytest.raises(ValueError):
            self.tool._validate_pid(0)
        print("✅ Zero PID rejected")


class TestPortExtraction:
    """Test port extraction"""
    
    def setup_method(self):
        """Setup"""
        self.sandbox = Mock()
        self.tool = WebDevTool(self.sandbox)
    
    def test_extract_port_various_formats(self):
        """Test port extraction from various formats"""
        test_cases = [
            ("python3 -m http.server 8080", 8080),
            ("npm run dev --port 3000", 3000),
            ("node server.js -p 5000", 5000),
            ("flask run --port=8888", 8888),
            ("uvicorn main:app --port 9000", 9000),
            ("python3 -m http.server", None),
        ]
        
        for command, expected in test_cases:
            result = self.tool._extract_port_from_command(command)
            assert result == expected, f"Failed for {command}"
        print(f"✅ Port extraction: {len(test_cases)} test cases passed")
    
    def test_extract_port_invalid_range(self):
        """Test port range validation"""
        # Port too low
        result = self.tool._extract_port_from_command("python3 -m http.server 80")
        assert result is None
        
        # Port too high
        result = self.tool._extract_port_from_command("python3 -m http.server 99999")
        assert result is None
        
        print("✅ Port range validation works")


class TestAsyncMethods:
    """Test async methods"""
    
    def setup_method(self):
        """Setup"""
        self.sandbox = AsyncMock()
        self.tool = WebDevTool(self.sandbox)
    
    @pytest.mark.asyncio
    async def test_get_process_start_time_success(self):
        """Test getting process start time"""
        self.sandbox.exec_command_stateful.return_value = {
            "exit_code": 0,
            "stdout": "12345",
            "stderr": ""
        }
        
        result = await self.tool._get_process_start_time(100)
        assert result is not None
        assert isinstance(result, float)
        print("✅ Get process start time succeeded")
    
    @pytest.mark.asyncio
    async def test_get_process_start_time_failure(self):
        """Test process not found"""
        self.sandbox.exec_command_stateful.return_value = {
            "exit_code": 1,
            "stdout": "",
            "stderr": "No such process"
        }
        
        result = await self.tool._get_process_start_time(99999)
        assert result is None
        print("✅ Non-existent process returns None")
    
    @pytest.mark.asyncio
    async def test_cleanup_empty(self):
        """Test cleanup with no servers"""
        result = await self.tool.cleanup()
        
        assert result["stopped_count"] == 0
        assert result["stopped_pids"] == []
        assert result["failed_pids"] == []
        print("✅ Cleanup with empty state works")


class TestConstants:
    """Test module constants"""
    
    def test_allowed_binaries(self):
        """Test ALLOWED_BINARIES is defined"""
        assert isinstance(ALLOWED_BINARIES, dict)
        assert len(ALLOWED_BINARIES) > 0
        assert 'python3' in ALLOWED_BINARIES
        assert 'npm' in ALLOWED_BINARIES
        print(f"✅ ALLOWED_BINARIES defined: {len(ALLOWED_BINARIES)} binaries")
    
    def test_limits(self):
        """Test limit constants"""
        assert MAX_LOG_READ_SIZE == 10 * 1024 * 1024  # 10 MB
        assert MAX_TOTAL_LOG_SIZE == 100 * 1024 * 1024  # 100 MB
        assert MAX_SERVERS_PER_TOOL == 10
        print("✅ Limit constants verified")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("WEBDEV.PY UNIT TESTS - COVERAGE ENHANCEMENT")
    print("="*70 + "\n")
    
    # Run with pytest
    exit_code = pytest.main([__file__, "-v", "-s", "--tb=short"])
    return exit_code


if __name__ == "__main__":
    exit(run_all_tests())
