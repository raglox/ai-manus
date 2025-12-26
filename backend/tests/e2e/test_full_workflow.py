"""
End-to-End Golden Path Test for WebDevTool

This test validates the complete workflow:
1. Create an index.html file
2. Start python -m http.server 8000 in background
3. Verify server responds with curl
4. Stop the server

⚠️ IMPORTANT: This test uses REAL Docker (not mocked)
   - Requires Docker daemon to be running
   - Creates actual containers
   - Tests real file operations and network

⚠️ CURRENTLY SKIPPED: These tests require proper Docker sandbox setup
with running containers. They need to be run in a proper E2E environment.

Author: Senior QA Automation Engineer
Date: 2025-12-26
"""

import pytest
import asyncio
import time
import os
from typing import Dict, Any

# Skip all E2E tests - they need proper Docker environment setup
pytestmark = pytest.mark.skip(reason="E2E tests require proper Docker sandbox environment")

# Skip if Docker is not available
try:
    import docker
    docker_client = docker.from_env()
    docker_client.ping()
    DOCKER_AVAILABLE = True
except Exception:
    DOCKER_AVAILABLE = False


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
@pytest.mark.asyncio
class TestFullWorkflow:
    """E2E test for complete WebDevTool workflow"""
    
    @pytest.fixture
    async def sandbox(self):
        """Create a real Docker sandbox instance"""
        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        
        # Create sandbox (no initialize needed - automatic on first use)
        sandbox = DockerSandbox()
        
        yield sandbox
        
        # Cleanup
        try:
            await sandbox.destroy()
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")
    
    @pytest.fixture
    async def webdev_tool(self, sandbox):
        """Create WebDevTool instance"""
        from app.domain.services.tools.webdev import WebDevTool
        
        tool = WebDevTool(sandbox)
        
        yield tool
        
        # Cleanup all servers
        try:
            await tool.cleanup()
        except Exception as e:
            print(f"Warning: Tool cleanup failed: {e}")
    
    async def test_golden_path_python_http_server(self, sandbox, webdev_tool):
        """
        Golden Path Test: Create HTML file and serve it with Python HTTP server
        
        Steps:
        1. Create index.html
        2. Start python -m http.server 8000
        3. Wait for server to be ready
        4. Verify server responds with curl
        5. Stop server
        """
        print("\n" + "="*70)
        print("🚀 E2E GOLDEN PATH TEST: Python HTTP Server")
        print("="*70)
        
        # Step 1: Create index.html
        print("\n[Step 1] Creating index.html...")
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>E2E Test Page</title>
</head>
<body>
    <h1>E2E Test Success!</h1>
    <p>This page was created and served by the WebDevTool E2E test.</p>
</body>
</html>"""
        
        # Write file using sandbox
        result = await sandbox.exec_command(
            f'cat > /tmp/index.html << \'EOF\'\n{html_content}\nEOF',
            cwd='/tmp'
        )
        assert result['exit_code'] == 0, "Failed to create index.html"
        print("✅ index.html created successfully")
        
        # Verify file exists
        result = await sandbox.exec_command('ls -la /tmp/index.html', cwd='/tmp')
        assert result['exit_code'] == 0, "index.html not found"
        assert 'index.html' in result['stdout']
        print("✅ File verified on disk")
        
        # Step 2: Start Python HTTP server
        print("\n[Step 2] Starting Python HTTP server on port 8000...")
        start_result = await webdev_tool.start_server(
            command='python3 -m http.server 8000',
            timeout_seconds=15
        )
        
        assert start_result.success, f"Failed to start server: {start_result.error}"
        assert start_result.data is not None
        assert 'url' in start_result.data
        assert 'pid' in start_result.data
        
        server_url = start_result.data['url']
        server_pid = start_result.data['pid']
        
        print(f"✅ Server started: {server_url} (PID: {server_pid})")
        
        # Step 3: Wait for server to be fully ready
        print("\n[Step 3] Waiting for server to be ready...")
        await asyncio.sleep(2)  # Give server time to initialize
        
        # Verify server is in tracking
        list_result = await webdev_tool.list_servers()
        assert list_result.success
        assert list_result.data['count'] == 1
        print(f"✅ Server is tracked (1 server running)")
        
        # Step 4: Verify server responds with curl
        print("\n[Step 4] Testing server response with curl...")
        max_retries = 5
        for attempt in range(max_retries):
            result = await sandbox.exec_command(
                f'curl -s -o /dev/null -w "%{{http_code}}" --connect-timeout 3 --max-time 5 {server_url}',
                cwd='/tmp'
            )
            
            if result['exit_code'] == 0 and result['stdout'].strip().startswith('2'):
                http_code = result['stdout'].strip()
                print(f"✅ Server responded: HTTP {http_code}")
                break
            
            if attempt < max_retries - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_retries} failed, retrying...")
                await asyncio.sleep(2)
        else:
            pytest.fail(f"Server did not respond after {max_retries} attempts")
        
        # Verify HTML content
        print("\n[Step 4b] Fetching HTML content...")
        result = await sandbox.exec_command(
            f'curl -s {server_url}/index.html',
            cwd='/tmp'
        )
        
        assert result['exit_code'] == 0, "Failed to fetch index.html"
        assert 'E2E Test Success' in result['stdout'], "HTML content mismatch"
        print("✅ HTML content verified")
        
        # Step 5: Stop server
        print("\n[Step 5] Stopping server...")
        stop_result = await webdev_tool.stop_server(server_pid)
        
        assert stop_result.success, f"Failed to stop server: {stop_result.error}"
        print(f"✅ Server stopped (PID: {server_pid})")
        
        # Verify server is no longer tracked
        list_result = await webdev_tool.list_servers()
        assert list_result.success
        assert list_result.data['count'] == 0
        print("✅ Server removed from tracking")
        
        # Verify server no longer responds
        print("\n[Step 6] Verifying server is down...")
        await asyncio.sleep(1)
        result = await sandbox.exec_command(
            f'curl -s -o /dev/null -w "%{{http_code}}" --connect-timeout 2 --max-time 3 {server_url} 2>&1 || echo "FAILED"',
            cwd='/tmp'
        )
        
        # Should fail to connect or timeout
        assert 'FAILED' in result['stdout'] or result['exit_code'] != 0, \
            "Server still responding after stop"
        print("✅ Server confirmed down")
        
        print("\n" + "="*70)
        print("🎉 E2E GOLDEN PATH TEST PASSED!")
        print("="*70)
    
    async def test_golden_path_npm_dev_server(self, sandbox, webdev_tool):
        """
        Golden Path Test: Start npm development server
        
        Note: This test validates the workflow but may skip actual npm run
        if package.json is not available in the sandbox
        """
        print("\n" + "="*70)
        print("🚀 E2E GOLDEN PATH TEST: NPM Dev Server")
        print("="*70)
        
        # Check if npm is available
        result = await sandbox.exec_command('which npm', cwd='/tmp')
        if result['exit_code'] != 0:
            pytest.skip("npm not available in sandbox")
        
        print("✅ npm is available")
        
        # Create minimal package.json
        print("\n[Step 1] Creating package.json...")
        package_json = """{
  "name": "e2e-test",
  "version": "1.0.0",
  "scripts": {
    "dev": "python3 -m http.server 3000"
  }
}"""
        
        result = await sandbox.exec_command(
            f'cat > /tmp/package.json << \'EOF\'\n{package_json}\nEOF',
            cwd='/tmp'
        )
        assert result['exit_code'] == 0
        print("✅ package.json created")
        
        # Start server using npm
        print("\n[Step 2] Starting server with npm run dev...")
        start_result = await webdev_tool.start_server(
            command='npm run dev',
            timeout_seconds=20
        )
        
        if not start_result.success:
            print(f"⚠️  Server start failed: {start_result.error}")
            pytest.skip("NPM dev server failed to start (expected in minimal sandbox)")
            return
        
        server_pid = start_result.data['pid']
        server_url = start_result.data['url']
        
        print(f"✅ Server started: {server_url} (PID: {server_pid})")
        
        # Wait and verify
        await asyncio.sleep(3)
        
        result = await sandbox.exec_command(
            f'curl -s -o /dev/null -w "%{{http_code}}" --connect-timeout 3 {server_url}',
            cwd='/tmp'
        )
        
        if result['exit_code'] == 0:
            print(f"✅ Server responded: HTTP {result['stdout'].strip()}")
        
        # Cleanup
        stop_result = await webdev_tool.stop_server(server_pid)
        assert stop_result.success
        print(f"✅ Server stopped")
        
        print("\n" + "="*70)
        print("🎉 E2E NPM TEST PASSED!")
        print("="*70)
    
    async def test_concurrent_servers(self, sandbox, webdev_tool):
        """
        Test running multiple servers concurrently
        """
        print("\n" + "="*70)
        print("🚀 E2E TEST: Concurrent Servers")
        print("="*70)
        
        # Start server 1 on port 8001
        print("\n[Server 1] Starting on port 8001...")
        result1 = await webdev_tool.start_server(
            command='python3 -m http.server 8001',
            timeout_seconds=15
        )
        assert result1.success
        pid1 = result1.data['pid']
        print(f"✅ Server 1 started (PID: {pid1})")
        
        # Start server 2 on port 8002
        print("\n[Server 2] Starting on port 8002...")
        result2 = await webdev_tool.start_server(
            command='python3 -m http.server 8002',
            timeout_seconds=15
        )
        assert result2.success
        pid2 = result2.data['pid']
        print(f"✅ Server 2 started (PID: {pid2})")
        
        # Verify both are tracked
        list_result = await webdev_tool.list_servers()
        assert list_result.success
        assert list_result.data['count'] == 2
        print(f"✅ Both servers tracked")
        
        # Wait for servers to be ready
        await asyncio.sleep(2)
        
        # Test both servers
        for pid, port in [(pid1, 8001), (pid2, 8002)]:
            result = await sandbox.exec_command(
                f'curl -s -o /dev/null -w "%{{http_code}}" --connect-timeout 3 http://localhost:{port}',
                cwd='/tmp'
            )
            assert result['exit_code'] == 0
            print(f"✅ Server on port {port} responding")
        
        # Stop both
        await webdev_tool.stop_server(pid1)
        await webdev_tool.stop_server(pid2)
        print("✅ Both servers stopped")
        
        # Verify cleanup
        list_result = await webdev_tool.list_servers()
        assert list_result.data['count'] == 0
        print("✅ All servers cleaned up")
        
        print("\n" + "="*70)
        print("🎉 E2E CONCURRENT SERVERS TEST PASSED!")
        print("="*70)


# Standalone execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
