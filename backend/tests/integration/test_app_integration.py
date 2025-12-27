"""
Application Integration Tests

These tests verify that major application components integrate correctly.
They don't require external Docker containers but test real integration points.

Run with: pytest tests/integration/test_app_integration.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

pytestmark = pytest.mark.integration


# Shared Beanie initialization state
_beanie_initialized = False
_beanie_lock = asyncio.Lock()


@pytest.fixture(scope="function", autouse=True)
async def ensure_beanie_init():
    """Auto-initialize Beanie once for all async tests"""
    global _beanie_initialized
    
    # Check if already initialized
    if _beanie_initialized:
        return
    
    async with _beanie_lock:
        # Double-check after acquiring lock
        if _beanie_initialized:
            return
            
        from beanie import init_beanie
        from app.infrastructure.storage.mongodb import get_mongodb
        from app.infrastructure.models.documents import (
            AgentDocument,
            SessionDocument, 
            UserDocument,
            SubscriptionDocument
        )
        from app.core.config import get_settings
        
        settings = get_settings()
        mongodb = get_mongodb()
        
        # Initialize MongoDB connection first
        await mongodb.initialize()
        print("\n✅ MongoDB connection initialized")
        
        # Now initialize Beanie ODM
        await init_beanie(
            database=mongodb.client[settings.mongodb_database],
            document_models=[AgentDocument, SessionDocument, UserDocument, SubscriptionDocument]
        )
        
        _beanie_initialized = True
        print("✅ Beanie ODM initialized for tests\n")


class TestDatabaseIntegration:
    """Test database integration"""
    
    @pytest.mark.asyncio
    async def test_mongodb_connection(self):
        """Test that MongoDB connection works"""
        from app.core.config import get_settings
        from motor.motor_asyncio import AsyncIOMotorClient
        
        settings = get_settings()
        
        # Create client
        client = AsyncIOMotorClient(settings.mongodb_uri)
        
        # Test connection
        try:
            # Ping database
            await client.admin.command('ping')
            print("✅ MongoDB connection successful")
            
            # List databases
            db_list = await client.list_database_names()
            assert len(db_list) > 0
            print(f"✅ Found {len(db_list)} databases")
            
        finally:
            client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_integration(self):
        """Test User repository with real database"""
        from app.infrastructure.repositories.user_repository import MongoUserRepository as UserRepository
        from app.domain.models.user import User, UserRole
        from datetime import datetime, UTC
        import uuid
        
        # Create repository
        repo = UserRepository()
        
        # Create test user
        test_email = f"integration_test_{uuid.uuid4().hex[:8]}@example.com"
        test_user = User(
            id=f"test_{uuid.uuid4().hex[:8]}",
            fullname="Integration Test User",
            email=test_email,
            password_hash="hashed_password_123",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        try:
            # Test create
            created_user = await repo.create_user(test_user)
            assert created_user is not None
            assert created_user.email == test_email
            print(f"✅ Created user: {created_user.id}")
            
            # Test find by email
            found_user = await repo.get_user_by_email(test_email)
            assert found_user is not None
            assert found_user.id == created_user.id
            print(f"✅ Found user by email: {found_user.id}")
            
            # Test find by id
            found_by_id = await repo.get_user_by_id(created_user.id)
            assert found_by_id is not None
            assert found_by_id.email == test_email
            print(f"✅ Found user by ID: {found_by_id.id}")
            
        finally:
            # Cleanup
            try:
                await repo.delete(test_user.id)
                print(f"✅ Cleaned up test user: {test_user.id}")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


class TestRedisIntegration:
    """Test Redis integration"""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test that Redis connection works"""
        from app.core.config import get_settings
        import redis.asyncio as aioredis
        
        settings = get_settings()
        
        # Build Redis URL
        redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        if settings.redis_password:
            redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        
        # Create client
        redis_client = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        try:
            # Test ping
            pong = await redis_client.ping()
            assert pong is True
            print("✅ Redis connection successful")
            
            # Test set/get
            test_key = "integration_test_key"
            test_value = "integration_test_value"
            
            await redis_client.set(test_key, test_value)
            result = await redis_client.get(test_key)
            assert result == test_value
            print("✅ Redis set/get working")
            
            # Cleanup
            await redis_client.delete(test_key)
            
        finally:
            await redis_client.close()


class TestAuthServiceIntegration:
    """Test Auth Service with real dependencies"""
    
    @pytest.mark.asyncio
    async def test_register_and_login_flow(self):
        """Test complete registration and login flow"""
        from app.application.services.auth_service import AuthService
        from app.infrastructure.repositories.user_repository import MongoUserRepository as UserRepository
        from app.application.services.token_service import TokenService
        import uuid
        
        # Create services
        user_repo = UserRepository()
        token_service = TokenService()
        auth_service = AuthService(user_repo, token_service)
        
        # Unique email for this test
        test_email = f"int_test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "SecurePassword123!"
        
        try:
            # Step 1: Register user
            registered_user = await auth_service.register_user(
                fullname="Integration Test",
                email=test_email,
                password=test_password
            )
            
            assert registered_user is not None
            assert registered_user.email == test_email
            print(f"✅ User registered: {registered_user.id}")
            
            # Step 2: Login with correct credentials
            auth_tokens = await auth_service.login_with_tokens(
                email=test_email,
                password=test_password
            )
            
            assert auth_tokens is not None
            assert auth_tokens.access_token is not None
            assert auth_tokens.refresh_token is not None
            print(f"✅ Login successful, got tokens")
            
            # Step 3: Verify token
            verified_user = await auth_service.verify_token(auth_tokens.access_token)
            assert verified_user is not None
            assert verified_user.email == test_email
            print(f"✅ Token verification successful")
            
        finally:
            # Cleanup
            from app.infrastructure.repositories.user_repository import MongoUserRepository as UserRepository
            repo = UserRepository()
            try:
                # Find user and delete
                user = await repo.find_by_email(test_email)
                if user:
                    await repo.delete(user.id)
                    print(f"✅ Cleaned up test user")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


class TestSessionServiceIntegration:
    """Test Session Service with real dependencies"""
    
    @pytest.fixture
    async def session_service(self):
        """Create Session Repository (no SessionService exists)"""
        # Initialize Beanie first

        
        from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
        
        return MongoSessionRepository()
    
    @pytest.mark.asyncio
    async def test_create_and_retrieve_session(self):
        """Test session creation and retrieval"""
        from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
        from app.domain.models.session import Session, SessionStatus
        from datetime import datetime, UTC
        import uuid
        
        # Create repository instance
        session_repo = MongoSessionRepository()
        
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        agent_id = f"test_agent_{uuid.uuid4().hex[:8]}"
        
        # Create session object
        session = Session(
            id=session_id,
            user_id=test_user_id,
            agent_id=agent_id,
            agent_type="integration_test",
            status=SessionStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        try:
            # Create session using repository (save method)
            await session_repo.save(session)
            print(f"✅ Session created: {session.id}")
            
            # Retrieve session
            retrieved = await session_repo.find_by_id(session_id)
            assert retrieved is not None
            assert retrieved.id == session_id
            assert retrieved.user_id == test_user_id
            print(f"✅ Session retrieved: {retrieved.id}")
            
            # Update session status
            await session_repo.update_status(session_id, SessionStatus.RUNNING)
            updated = await session_repo.find_by_id(session_id)
            assert updated.status == SessionStatus.RUNNING
            print(f"✅ Session status updated")
            
        finally:
            # Cleanup
            try:
                await session_repo.delete(session_id)
                print(f"✅ Session cleaned up")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


class TestFileServiceIntegration:
    """Test File Service with GridFS"""
    
    @pytest.mark.asyncio
    async def test_file_upload_download_cycle(self):
        """Test file upload and download"""
        from app.infrastructure.external.file.gridfsfile import GridFSFileStorage
        from app.infrastructure.storage.mongodb import get_mongodb
        from io import BytesIO
        import uuid
        
        # Get MongoDB instance
        mongodb = get_mongodb()
        
        # Create file service
        file_service = GridFSFileStorage(mongodb)
        
        # Test data
        test_content = b"Integration test file content"
        test_filename = f"integration_test_{uuid.uuid4().hex[:8]}.txt"
        file_stream = BytesIO(test_content)
        
        try:
            # Upload file
            file_info = await file_service.upload_file(
                file_stream, 
                test_filename,
                user_id="integration_test"
            )
            assert file_info is not None
            assert file_info.id is not None
            file_id = file_info.id
            print(f"✅ File uploaded: {file_id}")
            
            # Download file
            downloaded_stream, file_info = await file_service.download_file(
                file_id,
                user_id="integration_test"
            )
            assert downloaded_stream is not None
            
            # Verify content
            downloaded_content = downloaded_stream.read()
            assert downloaded_content == test_content
            print(f"✅ File downloaded and content verified")
            
            # Get file info
            file_info = await file_service.get_file_info(
                file_id,
                user_id="integration_test"
            )
            assert file_info is not None
            assert file_info.filename == test_filename
            print(f"✅ File metadata retrieved")
            
        finally:
            # Cleanup
            try:
                await file_service.delete_file(file_id, user_id="integration_test")
                print(f"✅ File cleaned up")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


class TestAPIEndpointsIntegration:
    """Test API endpoints integration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Health endpoint working: {data}")
    
    def test_docs_endpoint(self, client):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        print("✅ API docs endpoint working")
    
    def test_openapi_endpoint(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        print(f"✅ OpenAPI schema available with {len(schema['paths'])} paths")


class TestConfigurationIntegration:
    """Test configuration loading and validation"""
    
    def test_settings_load_successfully(self):
        """Test that settings load without errors"""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Verify critical settings
        assert settings.mongodb_uri is not None
        assert settings.redis_host is not None
        assert settings.jwt_secret_key is not None
        assert settings.auth_provider is not None
        
        print("✅ All critical settings loaded")
        print(f"   - Auth provider: {settings.auth_provider}")
        print(f"   - MongoDB: {settings.mongodb_uri}")
    
    def test_logging_configuration(self):
        """Test that logging is configured"""
        import logging
        
        # Get logger
        logger = logging.getLogger("app")
        
        # Verify logger exists and has handlers
        assert logger is not None
        assert len(logger.handlers) > 0 or len(logging.root.handlers) > 0
        
        print("✅ Logging configured")


class TestErrorHandlingIntegration:
    """Test error handling across the application"""
    
    @pytest.mark.asyncio
    async def test_auth_service_handles_duplicate_email(self):
        """Test that duplicate email registration fails gracefully"""
        from app.application.services.auth_service import AuthService
        from app.infrastructure.repositories.user_repository import MongoUserRepository as UserRepository
        from app.application.services.token_service import TokenService
        from app.application.errors.exceptions import BadRequestError
        import uuid
        
        user_repo = UserRepository()
        token_service = TokenService()
        auth_service = AuthService(user_repo, token_service)
        
        test_email = f"dup_test_{uuid.uuid4().hex[:8]}@example.com"
        
        try:
            # Register first user
            user1 = await auth_service.register_user(
                fullname="First User",
                email=test_email,
                password="Password123!"
            )
            print(f"✅ First user registered: {user1.id}")
            
            # Try to register second user with same email
            with pytest.raises(BadRequestError) as exc_info:
                await auth_service.register_user(
                    fullname="Second User",
                    email=test_email,
                    password="Password456!"
                )
            
            assert "already exists" in str(exc_info.value).lower()
            print("✅ Duplicate email properly rejected")
            
        finally:
            # Cleanup
            try:
                found_user = await user_repo.get_user_by_email(test_email)
                if found_user:
                    await user_repo.delete_user(found_user.id)
                    print("✅ Test user cleaned up")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


# Summary test
@pytest.mark.integration
class TestSystemIntegration:
    """High-level system integration verification"""
    
    @pytest.mark.asyncio
    async def test_full_stack_health(self):
        """Verify all major components are healthy"""
        from app.core.config import get_settings
        from motor.motor_asyncio import AsyncIOMotorClient
        import redis.asyncio as aioredis
        
        settings = get_settings()
        health_status = {}
        
        # Test MongoDB
        try:
            mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
            await mongo_client.admin.command('ping')
            health_status['mongodb'] = 'healthy'
            mongo_client.close()
        except Exception as e:
            health_status['mongodb'] = f'unhealthy: {e}'
        
        # Test Redis
        try:
            redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            if settings.redis_password:
                redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            redis_client = await aioredis.from_url(redis_url)
            await redis_client.ping()
            health_status['redis'] = 'healthy'
            await redis_client.close()
        except Exception as e:
            health_status['redis'] = f'unhealthy: {e}'
        
        # Test Application
        try:
            from app.main import app
            health_status['application'] = 'healthy'
        except Exception as e:
            health_status['application'] = f'unhealthy: {e}'
        
        # Print status
        print("\n" + "="*50)
        print("SYSTEM HEALTH STATUS")
        print("="*50)
        for component, status in health_status.items():
            status_emoji = "✅" if status == 'healthy' else "❌"
            print(f"{status_emoji} {component.upper()}: {status}")
        print("="*50)
        
        # Assert all healthy
        assert all(status == 'healthy' for status in health_status.values()), \
            f"Some components unhealthy: {health_status}"
        
        print("\n✅ Full stack integration verified!")
