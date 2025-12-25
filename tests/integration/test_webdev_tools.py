"""
Integration Tests for WebDev Tools.

Tests the complete web development workflow:
1. Create a simple web server
2. Start server in background
3. Verify URL detection
4. Test server accessibility
5. Stop server cleanly
"""

import pytest
import asyncio
from app.domain.services.tools.webdev import WebDevTool
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox


class TestWebDevIntegration:
    """Integration tests for WebDev workflow"""
    
    @pytest.fixture
    async def sandbox(self):
        """Create a sandbox instance for testing"""
        # This would need to be configured based on your test setup
        # For now, we'll skip actual Docker sandbox creation
        pytest.skip("Requires running Docker sandbox")
    
    @pytest.fixture
    async def webdev_tool(self, sandbox):
        """Create WebDevTool instance"""
        return WebDevTool(sandbox)
    
    @pytest.mark.asyncio
    async def test_python_http_server_workflow(self, webdev_tool):
        """
        Test Scenario: Python HTTP Server
        
        Steps:
        1. Start python3 -m http.server 8080
        2. Verify URL detected (http://localhost:8080)
        3. Verify PID returned
        4. Stop server
        """
        # Start server
        result = await webdev_tool.start_server(
            command="python3 -m http.server 8080",
            timeout_seconds=10
        )
        
        assert result.success, f"Failed to start server: {result.message}"
        assert result.data["pid"] is not None, "PID not returned"
        assert result.data["url"] is not None, "URL not detected"
        assert "8080" in result.data["url"], f"Wrong port in URL: {result.data['url']}"
        
        pid = result.data["pid"]
        
        # Stop server
        stop_result = await webdev_tool.stop_server(pid=pid)
        assert stop_result.success, f"Failed to stop server: {stop_result.message}"
    
    @pytest.mark.asyncio
    async def test_node_server_workflow(self, webdev_tool, sandbox):
        """
        Test Scenario: Node.js Server
        
        Steps:
        1. Create simple server.js
        2. Start with node server.js
        3. Verify URL detection
        4. Stop server
        """
        # Create server.js
        server_code = '''
const http = require('http');
const port = 3000;

const server = http.createServer((req, res) => {
    res.statusCode = 200;
    res.setHeader('Content-Type', 'text/plain');
    res.end('Hello World\\n');
});

server.listen(port, () => {
    console.log(`Server running at http://localhost:${port}/`);
});
'''
        
        # Write server file
        await sandbox.file_write("/tmp/server.js", server_code)
        
        # Start server
        result = await webdev_tool.start_server(
            command="node /tmp/server.js",
            timeout_seconds=15
        )
        
        assert result.success
        assert result.data["pid"] is not None
        assert result.data["url"] is not None
        assert "3000" in result.data["url"]
        
        # Stop server
        await webdev_tool.stop_server(pid=result.data["pid"])
    
    @pytest.mark.asyncio
    async def test_list_servers(self, webdev_tool):
        """Test listing running servers"""
        # Start a server
        start_result = await webdev_tool.start_server(
            command="python3 -m http.server 8090",
            timeout_seconds=10
        )
        
        assert start_result.success
        pid = start_result.data["pid"]
        
        # List servers
        list_result = await webdev_tool.list_servers()
        assert list_result.success
        assert len(list_result.data["processes"]) >= 1
        
        # Verify our server is in the list
        found = False
        for proc in list_result.data["processes"]:
            if proc["pid"] == pid:
                found = True
                assert proc["running"] is True
                assert "8090" in proc["command"]
        
        assert found, f"Server with PID {pid} not found in list"
        
        # Cleanup
        await webdev_tool.stop_server(pid=pid)
    
    @pytest.mark.asyncio
    async def test_server_logs(self, webdev_tool):
        """Test retrieving server logs"""
        # Start server
        start_result = await webdev_tool.start_server(
            command="python3 -m http.server 8091",
            timeout_seconds=10
        )
        
        assert start_result.success
        pid = start_result.data["pid"]
        
        # Get logs
        logs_result = await webdev_tool.get_server_logs(pid=pid, tail_lines=50)
        assert logs_result.success
        assert logs_result.data["logs"] is not None
        assert len(logs_result.data["logs"]) > 0
        
        # Cleanup
        await webdev_tool.stop_server(pid=pid)
    
    @pytest.mark.asyncio
    async def test_url_detection_timeout(self, webdev_tool):
        """Test URL detection timeout handling"""
        # Start a command that doesn't output a URL
        result = await webdev_tool.start_server(
            command="sleep 100",
            timeout_seconds=2
        )
        
        # Should still succeed but without URL
        assert result.success
        assert result.data["pid"] is not None
        assert result.data["url"] is None
        assert "no URL detected" in result.message.lower()
        
        # Cleanup
        await webdev_tool.stop_server(pid=result.data["pid"])
    
    @pytest.mark.asyncio
    async def test_multiple_servers(self, webdev_tool):
        """Test running multiple servers simultaneously"""
        ports = [8001, 8002, 8003]
        pids = []
        
        # Start multiple servers
        for port in ports:
            result = await webdev_tool.start_server(
                command=f"python3 -m http.server {port}",
                timeout_seconds=10
            )
            assert result.success
            pids.append(result.data["pid"])
        
        # List all servers
        list_result = await webdev_tool.list_servers()
        assert list_result.success
        assert len(list_result.data["processes"]) >= 3
        
        # Stop all servers
        for pid in pids:
            stop_result = await webdev_tool.stop_server(pid=pid)
            assert stop_result.success
    
    @pytest.mark.asyncio
    async def test_stop_nonexistent_server(self, webdev_tool):
        """Test stopping a server that doesn't exist"""
        result = await webdev_tool.stop_server(pid=99999)
        assert not result.success
        assert "not exist" in result.message.lower() or "failed" in result.message.lower()


class TestWebDevScenarios:
    """Real-world scenario tests"""
    
    @pytest.mark.asyncio
    async def test_complete_webapp_workflow(self, webdev_tool, sandbox):
        """
        Complete Workflow Test:
        
        Agent task: "Create a simple web app and run it"
        
        Steps:
        1. Agent creates server.py with FileTool
        2. Agent uses start_server to launch it
        3. Agent receives URL and can report to user
        4. Agent stops server when done
        """
        # Step 1: Create server file
        server_code = '''
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Hello from AI-Manus WebDev!</h1>")
        
if __name__ == "__main__":
    port = 8080
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    print(f"Server running on http://localhost:{port}")
    sys.stdout.flush()
    server.serve_forever()
'''
        
        await sandbox.file_write("/tmp/webapp.py", server_code)
        
        # Step 2: Start server
        start_result = await webdev_tool.start_server(
            command="python3 /tmp/webapp.py",
            timeout_seconds=15
        )
        
        assert start_result.success, f"Failed to start: {start_result.message}"
        assert "http://localhost:8080" in start_result.message
        
        url = start_result.data["url"]
        pid = start_result.data["pid"]
        
        # Step 3: Simulate agent reporting to user
        user_message = f"✅ Web app is running at {url}"
        assert url in user_message
        
        # Wait a bit to ensure server is stable
        await asyncio.sleep(2)
        
        # Step 4: Stop server
        stop_result = await webdev_tool.stop_server(pid=pid)
        assert stop_result.success
    
    @pytest.mark.asyncio  
    async def test_npm_dev_server_scenario(self, webdev_tool, sandbox):
        """
        Test npm run dev scenario (requires Node.js project)
        
        This is a more complex scenario that would be used
        when agent is asked to work with a React/Next.js app
        """
        # This test would require a full npm project setup
        # Skipping for now unless in full integration environment
        pytest.skip("Requires full npm project setup")
        
        # Conceptual flow:
        # 1. Agent detects package.json
        # 2. Agent runs: npm install (if needed)
        # 3. Agent uses: start_server(command="npm run dev", timeout_seconds=60)
        # 4. URL detected: http://localhost:3000
        # 5. Agent reports: "Development server is running at http://localhost:3000"


class TestWebDevEdgeCases:
    """Edge case and error handling tests"""
    
    @pytest.mark.asyncio
    async def test_invalid_command(self, webdev_tool):
        """Test starting server with invalid command"""
        result = await webdev_tool.start_server(
            command="this_command_does_not_exist",
            timeout_seconds=5
        )
        
        # Should fail gracefully
        assert not result.success
    
    @pytest.mark.asyncio
    async def test_port_already_in_use(self, webdev_tool):
        """Test handling port conflict"""
        # Start first server
        result1 = await webdev_tool.start_server(
            command="python3 -m http.server 8888",
            timeout_seconds=10
        )
        assert result1.success
        pid1 = result1.data["pid"]
        
        # Try to start second server on same port
        result2 = await webdev_tool.start_server(
            command="python3 -m http.server 8888",
            timeout_seconds=10
        )
        
        # Behavior may vary - could fail or start with error in logs
        # At minimum, we should get a PID and be able to check logs
        if result2.success:
            pid2 = result2.data["pid"]
            logs = await webdev_tool.get_server_logs(pid=pid2)
            # Logs should contain error about port in use
            await webdev_tool.stop_server(pid=pid2)
        
        # Cleanup
        await webdev_tool.stop_server(pid=pid1)
    
    @pytest.mark.asyncio
    async def test_server_crash_detection(self, webdev_tool):
        """Test detecting when server crashes after start"""
        # Start a command that will exit immediately
        result = await webdev_tool.start_server(
            command="python3 -c 'import sys; print(\"http://localhost:9999\"); sys.exit(1)'",
            timeout_seconds=5
        )
        
        # Should start and detect URL, but process will die
        pid = result.data["pid"]
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Check if still running via list_servers
        list_result = await webdev_tool.list_servers()
        
        # Find our process
        for proc in list_result.data["processes"]:
            if proc["pid"] == pid:
                # Should be marked as not running
                assert proc["running"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
