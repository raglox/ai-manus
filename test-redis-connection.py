#!/usr/bin/env python3
"""Quick Redis connectivity test"""
import asyncio
from redis.asyncio import Redis

async def test_redis():
    print("=== Redis Connection Test ===")
    print(f"Host: 10.236.19.107")
    print(f"Port: 6379")
    print(f"Password: None (no-password)")
    print("")
    
    try:
        print("Creating Redis client...")
        client = Redis(
            host="10.236.19.107",
            port=6379,
            db=0,
            password=None,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
        )
        
        print("Testing connection with ping...")
        response = await asyncio.wait_for(client.ping(), timeout=10.0)
        print(f"✅ SUCCESS! Redis ping response: {response}")
        
        await client.close()
        return True
        
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: Connection timed out")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_redis())
    exit(0 if result else 1)
