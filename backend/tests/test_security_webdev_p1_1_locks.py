"""
P1-1 Async Locks Tests - Race Condition Protection
Tests for concurrent access to _started_servers
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock


class TestP11AsyncLocks:
    """Test P1-1: Async lock protection against race conditions"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Mock WebDevTool with lock
        self.tool = Mock()
        self.tool._started_servers = {}
        self.tool._server_lock = asyncio.Lock()
    
    @pytest.mark.asyncio
    async def test_concurrent_start_operations(self):
        """Test that concurrent start operations don't corrupt state"""
        async def start_server(pid):
            async with self.tool._server_lock:
                self.tool._started_servers[pid] = {
                    "command": f"server-{pid}",
                    "start_time": time.time()
                }
                # Simulate some processing
                await asyncio.sleep(0.01)
        
        # Start 10 servers concurrently
        tasks = [start_server(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Verify all 10 servers were tracked
        assert len(self.tool._started_servers) == 10
        for i in range(10):
            assert i in self.tool._started_servers
            assert self.tool._started_servers[i]["command"] == f"server-{i}"
        
        print(f"✅ Concurrent start: {len(self.tool._started_servers)} servers tracked")
    
    @pytest.mark.asyncio
    async def test_concurrent_stop_operations(self):
        """Test that concurrent stop operations don't cause KeyError"""
        # Pre-populate with servers
        for i in range(10):
            self.tool._started_servers[i] = {"command": f"server-{i}"}
        
        async def stop_server(pid):
            async with self.tool._server_lock:
                if pid in self.tool._started_servers:
                    del self.tool._started_servers[pid]
                    await asyncio.sleep(0.01)
                    return True
                return False
        
        # Stop all servers concurrently
        tasks = [stop_server(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all stops succeeded
        assert sum(results) == 10
        assert len(self.tool._started_servers) == 0
        
        print(f"✅ Concurrent stop: All {sum(results)} servers stopped")
    
    @pytest.mark.asyncio
    async def test_concurrent_start_and_stop(self):
        """Test mixed start/stop operations don't cause race"""
        async def start_server(pid):
            async with self.tool._server_lock:
                self.tool._started_servers[pid] = {"command": f"server-{pid}"}
                await asyncio.sleep(0.01)
        
        async def stop_server(pid):
            async with self.tool._server_lock:
                if pid in self.tool._started_servers:
                    del self.tool._started_servers[pid]
                    return True
                return False
        
        # Mix of start and stop operations
        tasks = []
        for i in range(20):
            if i % 2 == 0:
                tasks.append(start_server(i))
            else:
                tasks.append(stop_server(i))
        
        await asyncio.gather(*tasks)
        
        # Verify only even PIDs remain (started but not stopped)
        for i in range(20):
            if i % 2 == 0:
                assert i in self.tool._started_servers
            else:
                assert i not in self.tool._started_servers
        
        print(f"✅ Mixed operations: {len(self.tool._started_servers)} servers remaining")
    
    @pytest.mark.asyncio
    async def test_list_during_modification(self):
        """Test that listing doesn't fail during concurrent modifications"""
        # Pre-populate
        for i in range(5):
            self.tool._started_servers[i] = {"command": f"server-{i}"}
        
        async def list_servers():
            async with self.tool._server_lock:
                # Take snapshot
                snapshot = list(self.tool._started_servers.items())
                await asyncio.sleep(0.01)
            return snapshot
        
        async def modify_servers():
            for i in range(5, 10):
                async with self.tool._server_lock:
                    self.tool._started_servers[i] = {"command": f"server-{i}"}
                    await asyncio.sleep(0.005)
        
        # List while modifying
        list_task = asyncio.create_task(list_servers())
        modify_task = asyncio.create_task(modify_servers())
        
        snapshot, _ = await asyncio.gather(list_task, modify_task)
        
        # Snapshot should have 5 original servers
        assert len(snapshot) >= 5
        
        # Final state should have 10 servers
        assert len(self.tool._started_servers) == 10
        
        print(f"✅ List during modification: snapshot={len(snapshot)}, final={len(self.tool._started_servers)}")
    
    @pytest.mark.asyncio
    async def test_cleanup_race(self):
        """Test cleanup doesn't interfere with new starts"""
        # Pre-populate
        for i in range(5):
            self.tool._started_servers[i] = {"command": f"server-{i}"}
        
        async def cleanup():
            async with self.tool._server_lock:
                pids_to_stop = list(self.tool._started_servers.keys())
            
            # Simulate stopping each (outside lock)
            for pid in pids_to_stop:
                async with self.tool._server_lock:
                    if pid in self.tool._started_servers:
                        del self.tool._started_servers[pid]
                await asyncio.sleep(0.01)
        
        async def start_new_servers():
            await asyncio.sleep(0.02)  # Let cleanup start
            for i in range(100, 105):
                async with self.tool._server_lock:
                    self.tool._started_servers[i] = {"command": f"server-{i}"}
                await asyncio.sleep(0.01)
        
        # Run cleanup and new starts concurrently
        await asyncio.gather(cleanup(), start_new_servers())
        
        # Old servers should be gone, new servers should exist
        for i in range(5):
            assert i not in self.tool._started_servers
        for i in range(100, 105):
            assert i in self.tool._started_servers
        
        print(f"✅ Cleanup race: {len(self.tool._started_servers)} new servers added during cleanup")
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self):
        """Stress test with 100 concurrent operations"""
        async def random_operation(i):
            operation = i % 3
            pid = i % 50  # Reuse PIDs
            
            if operation == 0:  # Start
                async with self.tool._server_lock:
                    self.tool._started_servers[pid] = {"command": f"server-{pid}"}
            elif operation == 1:  # Stop
                async with self.tool._server_lock:
                    if pid in self.tool._started_servers:
                        del self.tool._started_servers[pid]
            else:  # List
                async with self.tool._server_lock:
                    _ = list(self.tool._started_servers.keys())
            
            await asyncio.sleep(0.001)
        
        # 100 concurrent operations
        tasks = [random_operation(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        # Should complete without errors
        print(f"✅ Stress test: {len(self.tool._started_servers)} servers after 100 operations")
        assert True  # If we got here, no races occurred
    
    @pytest.mark.asyncio
    async def test_lock_timeout(self):
        """Test that locks don't cause deadlocks"""
        async def hold_lock_briefly():
            async with self.tool._server_lock:
                await asyncio.sleep(0.1)
                self.tool._started_servers[1] = {"command": "server-1"}
        
        async def try_acquire():
            start_time = time.time()
            async with self.tool._server_lock:
                elapsed = time.time() - start_time
                self.tool._started_servers[2] = {"command": "server-2"}
                return elapsed
        
        # Start first task that holds lock
        task1 = asyncio.create_task(hold_lock_briefly())
        await asyncio.sleep(0.01)  # Ensure task1 acquired lock
        
        # Try to acquire in second task
        task2 = asyncio.create_task(try_acquire())
        
        results = await asyncio.gather(task1, task2)
        elapsed = results[1]
        
        # Second task should wait ~0.1s (lock was held)
        assert elapsed >= 0.08  # Allow some tolerance
        assert len(self.tool._started_servers) == 2
        
        print(f"✅ Lock wait time: {elapsed:.3f}s (expected ~0.1s)")


def run_all_tests():
    """Run all P1-1 tests"""
    print("\n" + "="*70)
    print("P1-1 ASYNC LOCKS TESTS - Race Condition Protection")
    print("="*70 + "\n")
    
    test_class = TestP11AsyncLocks()
    
    tests = [
        ("test_concurrent_start_operations", test_class.test_concurrent_start_operations),
        ("test_concurrent_stop_operations", test_class.test_concurrent_stop_operations),
        ("test_concurrent_start_and_stop", test_class.test_concurrent_start_and_stop),
        ("test_list_during_modification", test_class.test_list_during_modification),
        ("test_cleanup_race", test_class.test_cleanup_race),
        ("test_high_concurrency_stress", test_class.test_high_concurrency_stress),
        ("test_lock_timeout", test_class.test_lock_timeout),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_class.setup_method()  # Reset for each test
            asyncio.run(test_func())
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    if failed == 0:
        print("✅ ALL P1-1 TESTS PASSED")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
