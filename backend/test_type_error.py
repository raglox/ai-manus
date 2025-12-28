import hashlib

def test_hashlib_type_error():
    print("--- Testing hashlib with string rounds ---")
    password = "DemoPass123!"
    salt = "_CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c"
    rounds = "100000" # String instead of int
    
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    try:
        # This should raise a TypeError
        hash_bytes = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, rounds)
        print(f"Hash created: {hash_bytes.hex()}")
    except TypeError as e:
        print(f"TypeError caught: {e}")
    except Exception as e:
        print(f"Other error caught: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_hashlib_type_error()