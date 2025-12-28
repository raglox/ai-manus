import hashlib
import base64
import os

def test_auth_service_hash():
    print("--- Testing AuthService Logic ---")
    password = "DemoPass123!"
    salt = "_CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c"
    rounds = 100000 # Updated default
    
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, rounds)
    result = salt + base64.b64encode(hash_bytes).decode('utf-8')
    print(f"AuthService Hash: {result}")

def test_prompt_hash():
    print("\n--- Testing Prompt Logic ---")
    password = "DemoPass123!"
    salt = "_CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c"
    
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    result = base64.b64encode(hashed).decode()
    print(f"Prompt Hash: {result}")

if __name__ == "__main__":
    test_auth_service_hash()
    test_prompt_hash()