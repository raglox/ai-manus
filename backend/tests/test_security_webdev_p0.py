"""
Security Tests for WebDevTools - P0 Fixes Validation

This test suite validates the P0 security fixes:
- P0-1: Enhanced command validation (LD_PRELOAD, args, paths)
- P0-2: PID start time tracking and recycling detection
- P0-3: Port ownership verification

Reference: ADVERSARIAL_SECURITY_AUDIT.md
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from app.domain.services.tools.webdev import WebDevTool
from app.domain.models.tool_result import ToolResult


class TestP01CommandValidation:
    """Test P0-1: Enhanced Command Validation (CVSS 9.8)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sandbox = Mock()
        self.webdev = WebDevTool(self.sandbox)
    
    def test_ld_preload_injection_blocked(self):
        """Test that LD_PRELOAD injection is blocked"""
        # Attack: LD_PRELOAD=/tmp/evil.so python3 server.py
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("LD_PRELOAD=/tmp/evil.so python3 server.py")
        
        assert "LD_PRELOAD" in str(exc_info.value)
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_ld_library_path_injection_blocked(self):
        """Test that LD_LIBRARY_PATH injection is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("LD_LIBRARY_PATH=/tmp python3 -m http.server 8080")
        
        assert "LD_LIBRARY_PATH" in str(exc_info.value)
    
    def test_path_injection_blocked(self):
        """Test that PATH injection is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("PATH=/tmp:$PATH npm run dev")
        
        assert "PATH" in str(exc_info.value)
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_python_c_argument_blocked(self):
        """Test that python -c (arbitrary code) is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("python3 -c 'import os; os.system(\"whoami\")'")
        
        assert "forbidden argument" in str(exc_info.value).lower()
        assert "-c" in str(exc_info.value)
    
    def test_node_eval_argument_blocked(self):
        """Test that node --eval is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("node --eval 'console.log(process.env)'")
        
        assert "forbidden argument" in str(exc_info.value).lower()
        assert "eval" in str(exc_info.value).lower()
    
    def test_perl_e_argument_blocked(self):
        """Test that perl -e is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("perl -e 'system(\"id\")'")
        
        # Note: perl not in ALLOWED_BINARIES, so will fail on whitelist first
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_absolute_path_blocked(self):
        """Test that absolute paths are blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("/tmp/python3 -m http.server 8080")
        
        assert "path" in str(exc_info.value).lower()
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_relative_path_blocked(self):
        """Test that relative paths are blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("./node server.js")
        
        assert "path" in str(exc_info.value).lower()
    
    def test_semicolon_injection_blocked(self):
        """Test that semicolon command chaining is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("python3 -m http.server 8080; whoami")
        
        assert ";" in str(exc_info.value)
        assert "dangerous" in str(exc_info.value).lower()
    
    def test_pipe_injection_blocked(self):
        """Test that pipe injection is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("python3 -m http.server 8080 | tee output.txt")
        
        assert "|" in str(exc_info.value)
        assert "dangerous" in str(exc_info.value).lower()
    
    def test_command_substitution_blocked(self):
        """Test that command substitution is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("python3 -m http.server $(echo 8080)")
        
        assert "$(" in str(exc_info.value)
    
    def test_backtick_substitution_blocked(self):
        """Test that backtick substitution is blocked"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("python3 -m http.server `echo 8080`")
        
        assert "`" in str(exc_info.value)
    
    def test_valid_commands_pass(self):
        """Test that valid commands pass validation"""
        valid_commands = [
            "python3 -m http.server 8080",
            "npm run dev",
            "node server.js",
            "flask run --port 5000",
            "uvicorn main:app --reload --port 8000",
        ]
        
        for cmd in valid_commands:
            try:
                self.webdev._validate_command(cmd)
            except ValueError as e:
                pytest.fail(f"Valid command rejected: {cmd}. Error: {e}")
    
    def test_command_not_in_whitelist(self):
        """Test that non-whitelisted commands are rejected"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("malicious-binary --serve")
        
        assert "not allowed" in str(exc_info.value).lower()
        assert "malicious-binary" in str(exc_info.value)
    
    def test_empty_command_rejected(self):
        """Test that empty commands are rejected"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("")
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_whitespace_only_command_rejected(self):
        """Test that whitespace-only commands are rejected"""
        with pytest.raises(ValueError) as exc_info:
            self.webdev._validate_command("   \t\n  ")
        
        assert "empty" in str(exc_info.value).lower()


class TestP02PIDTracking:
    """Test P0-2: PID Start Time Tracking (CVSS 9.1)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sandbox = Mock()
        self.sandbox.exec_command_stateful = AsyncMock()
        self.sandbox.kill_background_process = AsyncMock()
        self.webdev = WebDevTool(self.sandbox)
    
    @pytest.mark.asyncio
    async def test_pid_start_time_tracked(self):
        """Test that PID start time is tracked"""
        # Mock successful server start
        self.sandbox.exec_command_stateful.return_value = {
            "exit_code": 0,
            "stdout": "12345",  # elapsed time in seconds
            "stderr": ""
        }
        
        start_time = await self.webdev._get_process_start_time(12345)
        
        assert start_time is not None
        assert isinstance(start_time, float)
        # Should be close to current time minus elapsed
        assert abs(start_time - (time.time() - 12345)) < 2.0
    
    @pytest.mark.asyncio
    async def test_pid_not_found_returns_none(self):
        """Test that non-existent PID returns None"""
        self.sandbox.exec_command_stateful.return_value = {
            "exit_code": 1,
            "stdout": "",
            "stderr": "No such process"
        }
        
        start_time = await self.webdev._get_process_start_time(99999)
        
        assert start_time is None
    
    @pytest.mark.asyncio
    async def test_pid_recycling_detected(self):
        """Test that PID recycling is detected and blocked"""
        # Setup: Add a tracked server with old start time
        old_start_time = time.time() - 3600  # 1 hour ago
        self.webdev._started_servers[12345] = {
            "command": "python3 -m http.server 8080",
            "start_time": old_start_time,
            "session_id": "default"
        }
        
        # Mock: Process exists but with recent start time (PID was recycled)
        self.sandbox.exec_command_stateful.return_value = {
            "exit_code": 0,
            "stdout": "5",  # Started 5 seconds ago
            "stderr": ""
        }
        
        # Try to stop - should detect recycling
        result = await self.webdev.stop_server(12345)
        
        assert not result.success
        assert "recycling" in result.message.lower() or "start time" in result.message.lower()
        assert result.data.get("security_alert") == True
    
    @pytest.mark.asyncio
    async def test_untracked_pid_rejected(self):
        """Test that stopping untracked PID is rejected"""
        result = await self.webdev.stop_server(99999)
        
        assert not result.success
        assert "not tracked" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_stop_server_validates_ownership(self):
        """Test that stop_server validates PID ownership"""
        # Try to stop PID that's not in tracking
        result = await self.webdev.stop_server(12345)
        
        assert not result.success
        assert result.data.get("tracked") == False


class TestP03PortVerification:
    """Test P0-3: Port Ownership Verification (CVSS 9.3)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sandbox = Mock()
        self.sandbox.exec_command_stateful = AsyncMock()
        self.webdev = WebDevTool(self.sandbox)
    
    def test_extract_port_from_command(self):
        """Test port extraction from various command formats"""
        test_cases = [
            ("python3 -m http.server 8080", 8080),
            ("npm run dev --port 3000", 3000),
            ("node server.js -p 5000", 5000),
            ("flask run --port=8888", 8888),
            ("uvicorn main:app --port 9000", 9000),
            ("python3 -m http.server", None),  # No port specified
        ]
        
        for command, expected_port in test_cases:
            result = self.webdev._extract_port_from_command(command)
            assert result == expected_port, f"Failed for: {command}"
    
    @pytest.mark.asyncio
    async def test_port_listening_verification(self):
        """Test that port listening is verified"""
        # Mock: Port is listening
        self.sandbox.exec_command_stateful.side_effect = [
            {"exit_code": 0, "stdout": "tcp 0.0.0.0:8080 LISTEN", "stderr": ""},  # netstat
            {"exit_code": 0, "stdout": "12345", "stderr": ""},  # lsof
            {"exit_code": 0, "stdout": "200", "stderr": ""},  # curl
        ]
        
        result = await self.webdev._verify_port_listening(12345, "http://localhost:8080")
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_port_not_listening_fails(self):
        """Test that non-listening port fails verification"""
        # Mock: Port is NOT listening
        self.sandbox.exec_command_stateful.return_value = {
            "exit_code": 1,
            "stdout": "not_found",
            "stderr": ""
        }
        
        result = await self.webdev._verify_port_listening(12345, "http://localhost:8080")
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_port_hijacking_detected(self):
        """Test that port hijacking is detected"""
        # Mock: Port is listening but owned by different PID
        self.sandbox.exec_command_stateful.side_effect = [
            {"exit_code": 0, "stdout": "tcp 0.0.0.0:8080 LISTEN", "stderr": ""},  # netstat - port listening
            {"exit_code": 0, "stdout": "99999", "stderr": ""},  # lsof - different PID!
        ]
        
        result = await self.webdev._verify_port_listening(12345, "http://localhost:8080")
        
        # Should fail because PID doesn't match
        assert result == False
    
    @pytest.mark.asyncio
    async def test_lsof_not_available_continues(self):
        """Test that verification continues if lsof is not available"""
        # Mock: Port listening, but lsof not found
        self.sandbox.exec_command_stateful.side_effect = [
            {"exit_code": 0, "stdout": "tcp 0.0.0.0:8080 LISTEN", "stderr": ""},  # netstat - OK
            {"exit_code": 1, "stdout": "not_found", "stderr": ""},  # lsof - not available
            {"exit_code": 0, "stdout": "200", "stderr": ""},  # curl - OK
        ]
        
        result = await self.webdev._verify_port_listening(12345, "http://localhost:8080")
        
        # Should still pass (with warning logged)
        assert result == True


class TestIntegrationScenarios:
    """Integration tests for complete attack scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sandbox = Mock()
        self.sandbox.exec_command_stateful = AsyncMock()
        self.sandbox.kill_background_process = AsyncMock()
        self.webdev = WebDevTool(self.sandbox)
    
    @pytest.mark.asyncio
    async def test_full_ld_preload_attack_blocked(self):
        """Test complete LD_PRELOAD attack scenario is blocked"""
        # Attacker tries to inject malicious library
        malicious_commands = [
            "LD_PRELOAD=/tmp/evil.so python3 -m http.server 8080",
            "LD_LIBRARY_PATH=/tmp python3 server.py",
            "PYTHONPATH=/tmp/malicious python3 -m http.server 8080",
        ]
        
        for cmd in malicious_commands:
            with pytest.raises(ValueError):
                self.webdev._validate_command(cmd)
    
    @pytest.mark.asyncio
    async def test_full_argument_injection_blocked(self):
        """Test complete argument injection attack is blocked"""
        malicious_commands = [
            "python3 -c 'import os; os.system(\"cat /etc/passwd\")'",
            "node --eval 'require(\"child_process\").exec(\"reverse_shell\")'",
            "python3 --interactive -m http.server",
        ]
        
        for cmd in malicious_commands:
            with pytest.raises(ValueError):
                self.webdev._validate_command(cmd)
    
    @pytest.mark.asyncio
    async def test_full_path_traversal_blocked(self):
        """Test complete path traversal attack is blocked"""
        malicious_commands = [
            "/tmp/fake_python3 -m http.server 8080",
            "./malicious_node server.js",
            "../../../usr/bin/python3 -m http.server",
        ]
        
        for cmd in malicious_commands:
            with pytest.raises(ValueError):
                self.webdev._validate_command(cmd)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
