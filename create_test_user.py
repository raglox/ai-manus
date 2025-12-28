#!/usr/bin/env python3
"""Create test user directly in MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import hashlib
import secrets

# MongoDB connection
MONGODB_URI = "mongodb+srv://jadjadhos5_db_user:05vYi9XJkEPLGTHF@cluster0.9h9x33.mongodb.net/manus?retryWrites=true&w=majority"
PASSWORD_SALT = "_CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c"

def hash_password(password: str, salt: str) -> str:
    """Hash password using PBKDF2-SHA256"""
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 10)
    return salt + hash_bytes.hex()

async def create_test_user():
    """Create test user in MongoDB"""
    print("=== Creating Test User in MongoDB ===")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['manus']
    users_collection = db['users']
    
    # User data
    user_id = secrets.token_urlsafe(16)
    email = "test@manus.ai"
    password = "TestPass123!"
    fullname = "Test User"
    
    # Hash password
    password_hash = hash_password(password, PASSWORD_SALT)
    
    # Check if user exists
    existing = await users_collection.find_one({"email": email})
    if existing:
        print(f"User {email} already exists!")
        print(f"User ID: {existing.get('user_id')}")
        client.close()
        return existing.get('user_id')
    
    # Create user document
    user_doc = {
        "user_id": user_id,
        "fullname": fullname,
        "email": email.lower(),
        "password_hash": password_hash,
        "role": "user",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert user
    result = await users_collection.insert_one(user_doc)
    print(f"✅ User created successfully!")
    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"MongoDB _id: {result.inserted_id}")
    
    client.close()
    return user_id

if __name__ == "__main__":
    asyncio.run(create_test_user())
