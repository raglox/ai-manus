"""
Security Unit Tests for WebDevTools P0 Fixes
Standalone tests that verify security logic without full module dependencies
"""

import re
import shlex


class TestCommandValidationLogic:
    """Test P0-1 command validation logic directly"""
    
    # Replicate core validation logic from webdev.py
    ALLOWED_BINARIES = {
        'npm', 'node', 'python', 'python3', 'flask', 'uvicorn', 
        'gunicorn', 'django-admin', 'php', 'ruby', 'rails', 
        'deno', 'bun', 'pnpm', 'yarn', 'next', 'vite', 'webpack-dev-server'
    }
    
    FORBIDDEN_ARGS = {'-c', '--eval', '--interactive', '-e', 'exec', 'eval'}
    FORBIDDEN_ENV_VARS = {'LD_PRELOAD', 'LD_LIBRARY_PATH', 'PATH', 'PYTHONPATH'}
    DANGEROUS_CHARS = {';', '|', '&', '$', '`', '\\n', '\\r'}
    
    def validate_command(self, command: str) -> bool:
        """Replicate validation logic"""
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")
        
        # Check for dangerous shell characters
        for char in self.DANGEROUS_CHARS:
            if char in command:
                raise ValueError(f"Dangerous character found: {char}")
        
        # Parse command
        try:
            parts = shlex.split(command)
        except Exception as e:
            raise ValueError(f"Failed to parse command: {e}")
        
        if not parts:
            raise ValueError("Empty command after parsing")
        
        binary = parts[0]
        
        # Check for path in binary (absolute or relative)
        if '/' in binary or '.' in binary:
            raise ValueError(f"Path not allowed in binary: {binary}")
        
        # Check if binary is whitelisted
        if binary not in self.ALLOWED_BINARIES:
            raise ValueError(f"Binary '{binary}' not allowed. Allowed: {sorted(self.ALLOWED_BINARIES)}")
        
        # Check for forbidden arguments
        for arg in parts[1:]:
            if arg in self.FORBIDDEN_ARGS:
                raise ValueError(f"Forbidden argument: {arg}")
        
        # Check for environment variable injection
        for env_var in self.FORBIDDEN_ENV_VARS:
            if env_var in command:
                raise ValueError(f"Forbidden environment variable: {env_var}")
        
        return True
    
    def test_ld_preload_blocked(self):
        """Test LD_PRELOAD injection is blocked"""
        try:
            self.validate_command("LD_PRELOAD=/tmp/evil.so python3 server.py")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "LD_PRELOAD" in str(e)
            print(f"✅ LD_PRELOAD blocked: {e}")
    
    def test_ld_library_path_blocked(self):
        """Test LD_LIBRARY_PATH injection is blocked"""
        try:
            self.validate_command("LD_LIBRARY_PATH=/tmp python3 -m http.server")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "LD_LIBRARY_PATH" in str(e)
            print(f"✅ LD_LIBRARY_PATH blocked: {e}")
    
    def test_path_injection_blocked(self):
        """Test PATH injection is blocked"""
        try:
            self.validate_command("PATH=/tmp:$PATH npm run dev")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            # Can fail on PATH env var OR on $ dangerous char
            assert "PATH" in str(e) or "$" in str(e) or "Dangerous" in str(e)
            print(f"✅ PATH injection blocked: {e}")
    
    def test_python_c_blocked(self):
        """Test python -c is blocked"""
        try:
            self.validate_command("python3 -c 'import os'")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "-c" in str(e) or "Forbidden" in str(e)
            print(f"✅ python -c blocked: {e}")
    
    def test_node_eval_blocked(self):
        """Test node --eval is blocked"""
        try:
            self.validate_command("node --eval 'console.log(1)'")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "eval" in str(e).lower()
            print(f"✅ node --eval blocked: {e}")
    
    def test_absolute_path_blocked(self):
        """Test absolute path is blocked"""
        try:
            self.validate_command("/tmp/python3 -m http.server")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Path" in str(e) or "/" in str(e)
            print(f"✅ Absolute path blocked: {e}")
    
    def test_relative_path_blocked(self):
        """Test relative path is blocked"""
        try:
            self.validate_command("./node server.js")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Path" in str(e) or "." in str(e)
            print(f"✅ Relative path blocked: {e}")
    
    def test_semicolon_blocked(self):
        """Test semicolon command chaining is blocked"""
        try:
            self.validate_command("python3 -m http.server; whoami")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert ";" in str(e) or "Dangerous" in str(e)
            print(f"✅ Semicolon blocked: {e}")
    
    def test_pipe_blocked(self):
        """Test pipe is blocked"""
        try:
            self.validate_command("python3 -m http.server | tee output.txt")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "|" in str(e) or "Dangerous" in str(e)
            print(f"✅ Pipe blocked: {e}")
    
    def test_command_substitution_blocked(self):
        """Test command substitution is blocked"""
        try:
            self.validate_command("python3 -m http.server $(echo 8080)")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "$" in str(e) or "Dangerous" in str(e)
            print(f"✅ Command substitution blocked: {e}")
    
    def test_backtick_blocked(self):
        """Test backtick substitution is blocked"""
        try:
            self.validate_command("python3 -m http.server `echo 8080`")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "`" in str(e) or "Dangerous" in str(e)
            print(f"✅ Backtick blocked: {e}")
    
    def test_valid_commands_pass(self):
        """Test valid commands pass"""
        valid_commands = [
            "python3 -m http.server 8080",
            "npm run dev",
            "node server.js",
            "flask run --port 5000",
            "uvicorn main:app --reload --port 8000",
        ]
        
        for cmd in valid_commands:
            try:
                result = self.validate_command(cmd)
                assert result == True
                print(f"✅ Valid command accepted: {cmd}")
            except ValueError as e:
                assert False, f"Valid command rejected: {cmd}. Error: {e}"
    
    def test_non_whitelisted_binary_blocked(self):
        """Test non-whitelisted binaries are rejected"""
        try:
            self.validate_command("malicious-binary --serve")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not allowed" in str(e).lower()
            print(f"✅ Non-whitelisted binary blocked: {e}")


class TestPortExtractionLogic:
    """Test P0-3 port extraction logic"""
    
    def extract_port(self, command: str) -> int:
        """Extract port from command"""
        patterns = [
            r':(\d+)',  # :8080
            r'\b(\d{4,5})\b',  # standalone 8080
            r'--port[=\s]+(\d+)',  # --port 8080 or --port=8080
            r'-p\s+(\d+)',  # -p 8080
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                port = int(match.group(1))
                if 1024 <= port <= 65535:
                    return port
        
        return None
    
    def test_port_extraction_formats(self):
        """Test port extraction from various formats"""
        test_cases = [
            ("python3 -m http.server 8080", 8080),
            ("npm run dev --port 3000", 3000),
            ("node server.js -p 5000", 5000),
            ("flask run --port=8888", 8888),
            ("uvicorn main:app --port 9000", 9000),
            ("python3 -m http.server", None),
        ]
        
        for command, expected_port in test_cases:
            result = self.extract_port(command)
            assert result == expected_port, f"Failed for: {command}. Got {result}, expected {expected_port}"
            if result:
                print(f"✅ Port extracted: {command} -> {result}")
            else:
                print(f"✅ No port found (expected): {command}")
    
    def test_port_range_validation(self):
        """Test port range validation"""
        # Ports below 1024 should be rejected
        result = self.extract_port("python3 -m http.server 80")
        assert result is None, "Port 80 should be rejected (< 1024)"
        print("✅ Port < 1024 rejected")
        
        # Ports above 65535 should be rejected
        result = self.extract_port("python3 -m http.server 99999")
        assert result is None, "Port 99999 should be rejected (> 65535)"
        print("✅ Port > 65535 rejected")
        
        # Valid range
        result = self.extract_port("python3 -m http.server 8080")
        assert result == 8080, "Port 8080 should be accepted"
        print("✅ Valid port accepted: 8080")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("P0 SECURITY TESTS - Command Validation & Port Extraction")
    print("="*70 + "\n")
    
    # Test P0-1: Command Validation
    print("\n📋 P0-1: Enhanced Command Validation Tests")
    print("-" * 70)
    cmd_tests = TestCommandValidationLogic()
    
    test_methods = [
        cmd_tests.test_ld_preload_blocked,
        cmd_tests.test_ld_library_path_blocked,
        cmd_tests.test_path_injection_blocked,
        cmd_tests.test_python_c_blocked,
        cmd_tests.test_node_eval_blocked,
        cmd_tests.test_absolute_path_blocked,
        cmd_tests.test_relative_path_blocked,
        cmd_tests.test_semicolon_blocked,
        cmd_tests.test_pipe_blocked,
        cmd_tests.test_command_substitution_blocked,
        cmd_tests.test_backtick_blocked,
        cmd_tests.test_valid_commands_pass,
        cmd_tests.test_non_whitelisted_binary_blocked,
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_method.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_method.__name__}: {e}")
            failed += 1
    
    # Test P0-3: Port Extraction
    print("\n📋 P0-3: Port Extraction Tests")
    print("-" * 70)
    port_tests = TestPortExtractionLogic()
    
    port_test_methods = [
        port_tests.test_port_extraction_formats,
        port_tests.test_port_range_validation,
    ]
    
    for test_method in port_test_methods:
        try:
            test_method()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_method.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_method.__name__}: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
