import jwt
import os
from datetime import datetime, timedelta

def test_jwt():
    print("--- Testing JWT Logic ---")
    secret = "7fa259ac28c4779014373b83cba325178098a725e36d5cd1cddeb7a4bfe8a0c5"
    
    payload = {
        "sub": "test_user_id",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "type": "access"
    }
    
    try:
        token = jwt.encode(payload, secret, algorithm="HS256")
        print(f"Token created: {token[:50]}...")
        
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        print(f"Token decoded: {decoded}")
    except Exception as e:
        print(f"JWT Error: {e}")

if __name__ == "__main__":
    test_jwt()