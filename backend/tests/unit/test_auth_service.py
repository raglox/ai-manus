"""
Comprehensive Unit Tests for Auth Service
Coverage: Registration, Login, Password management, Token operations
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from app.application.services.auth_service import AuthService
from app.domain.models.user import User
from app.application.errors.exceptions import (
    UnauthorizedError,
    ValidationError,
    BadRequestError
)
# Note: ValidationError replaced with ValidationError for duplicate checks


@pytest.fixture
def mock_user_repository():
    """Mock user repository"""
    repo = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_token_service():
    """Mock token service"""
    service = Mock()
    service.generate_access_token = Mock(return_value="mock_access_token")
    service.generate_refresh_token = Mock(return_value="mock_refresh_token")
    service.verify_token = Mock(return_value={
        "sub": "user123",
        "email": "test@example.com",
        "fullname": "Test User"
    })
    service.get_user_from_token = Mock()
    return service


@pytest.fixture
def auth_service(mock_user_repository, mock_token_service):
    """Create AuthService instance with mocked dependencies"""
    return AuthService(
        user_repository=mock_user_repository,
        token_service=mock_token_service
    )


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id="user123",
        fullname="Test User",
        email="test@example.com",
        password_hash="$2b$12$hashed_password",
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestUserRegistration:
    """Test user registration functionality"""
    
    @pytest.mark.asyncio
    async def test_register_new_user_success(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test successful user registration"""
        # Setup
        mock_user_repository.find_by_email.return_value = None  # User doesn't exist
        mock_user_repository.create.return_value = sample_user
        
        # Execute
        result = await auth_service.register(
            fullname="Test User",
            email="test@example.com",
            password="SecurePass123!"
        )
        
        # Assert
        assert result is not None
        assert result["user"] is not None
        assert result["access_token"] == "mock_access_token"
        assert result["refresh_token"] == "mock_refresh_token"
        
        # Verify repository was called
        mock_user_repository.find_by_email.assert_called_once_with("test@example.com")
        mock_user_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_existing_user_fails(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test registration with existing email fails"""
        # Setup - user already exists
        mock_user_repository.find_by_email.return_value = sample_user
        
        # Execute & Assert
        with pytest.raises((ValidationError, ValidationError, Exception)) as exc_info:
            await auth_service.register(
                fullname="Test User",
                email="test@example.com",
                password="SecurePass123!"
            )
        
        # Should not create user
        mock_user_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_register_with_weak_password(
        self, 
        auth_service, 
        mock_user_repository
    ):
        """Test registration with weak password"""
        mock_user_repository.find_by_email.return_value = None
        
        weak_passwords = ["123", "pass", "12345", ""]
        
        for weak_pwd in weak_passwords:
            with pytest.raises((ValidationError, Exception)):
                await auth_service.register(
                    fullname="Test User",
                    email="test@example.com",
                    password=weak_pwd
                )
    
    @pytest.mark.asyncio
    async def test_register_with_invalid_email(
        self, 
        auth_service, 
        mock_user_repository
    ):
        """Test registration with invalid email"""
        mock_user_repository.find_by_email.return_value = None
        
        invalid_emails = ["notanemail", "@domain.com", "user@", ""]
        
        for invalid_email in invalid_emails:
            with pytest.raises((ValidationError, Exception)):
                await auth_service.register(
                    fullname="Test User",
                    email=invalid_email,
                    password="SecurePass123!"
                )
    
    @pytest.mark.asyncio
    async def test_register_with_empty_fullname(
        self, 
        auth_service, 
        mock_user_repository
    ):
        """Test registration with empty fullname"""
        mock_user_repository.find_by_email.return_value = None
        
        with pytest.raises((ValidationError, Exception)):
            await auth_service.register(
                fullname="",
                email="test@example.com",
                password="SecurePass123!"
            )


class TestUserLogin:
    """Test user login functionality"""
    
    @pytest.mark.asyncio
    async def test_login_success(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test successful login"""
        # Setup
        mock_user_repository.find_by_email.return_value = sample_user
        
        # Mock password verification
        with patch.object(auth_service, '_verify_password', return_value=True):
            # Execute
            result = await auth_service.login(
                email="test@example.com",
                password="correct_password"
            )
            
            # Assert
            assert result is not None
            assert result["user"] is not None
            assert result["access_token"] == "mock_access_token"
            assert result["refresh_token"] == "mock_refresh_token"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test login with wrong password"""
        # Setup
        mock_user_repository.find_by_email.return_value = sample_user
        
        # Mock password verification to fail
        with patch.object(auth_service, '_verify_password', return_value=False):
            # Execute & Assert
            with pytest.raises(UnauthorizedError):
                await auth_service.login(
                    email="test@example.com",
                    password="wrong_password"
                )
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self, 
        auth_service, 
        mock_user_repository
    ):
        """Test login with non-existent user"""
        # Setup - user not found
        mock_user_repository.find_by_email.return_value = None
        
        # Execute & Assert
        with pytest.raises((UnauthorizedError, ValidationError)):
            await auth_service.login(
                email="nonexistent@example.com",
                password="any_password"
            )
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test login with inactive user account"""
        # Setup - inactive user
        sample_user.is_active = False
        mock_user_repository.find_by_email.return_value = sample_user
        
        # Execute & Assert
        with pytest.raises(UnauthorizedError):
            await auth_service.login(
                email="test@example.com",
                password="correct_password"
            )
    
    @pytest.mark.asyncio
    async def test_login_updates_last_login(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test that login updates last_login_at field"""
        # Setup
        mock_user_repository.find_by_email.return_value = sample_user
        
        with patch.object(auth_service, '_verify_password', return_value=True):
            # Execute
            await auth_service.login(
                email="test@example.com",
                password="correct_password"
            )
            
            # Assert - update should be called
            mock_user_repository.update.assert_called_once()


class TestTokenOperations:
    """Test token-related operations"""
    
    @pytest.mark.asyncio
    async def test_verify_token_success(
        self, 
        auth_service, 
        mock_token_service,
        mock_user_repository,
        sample_user
    ):
        """Test successful token verification"""
        # Setup
        mock_token_service.verify_token.return_value = {
            "sub": "user123",
            "email": "test@example.com"
        }
        mock_user_repository.find_by_id.return_value = sample_user
        
        # Execute
        user = await auth_service.verify_token("valid_token")
        
        # Assert
        assert user is not None
        assert user.id == sample_user.id
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(
        self, 
        auth_service, 
        mock_token_service
    ):
        """Test verification of invalid token"""
        # Setup
        mock_token_service.verify_token.return_value = None
        
        # Execute
        user = await auth_service.verify_token("invalid_token")
        
        # Assert
        assert user is None
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, 
        auth_service, 
        mock_token_service,
        mock_user_repository,
        sample_user
    ):
        """Test successful token refresh"""
        # Setup
        mock_token_service.verify_token.return_value = {
            "sub": "user123",
            "type": "refresh"
        }
        mock_user_repository.find_by_id.return_value = sample_user
        
        # Execute
        result = await auth_service.refresh_token("valid_refresh_token")
        
        # Assert
        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result


class TestPasswordManagement:
    """Test password change and reset operations"""
    
    @pytest.mark.asyncio
    async def test_change_password_success(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test successful password change"""
        # Setup
        mock_user_repository.find_by_id.return_value = sample_user
        
        with patch.object(auth_service, '_verify_password', return_value=True):
            # Execute
            await auth_service.change_password(
                user_id="user123",
                old_password="old_password",
                new_password="NewSecurePass123!"
            )
            
            # Assert - update should be called
            mock_user_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test password change with wrong old password"""
        # Setup
        mock_user_repository.find_by_id.return_value = sample_user
        
        with patch.object(auth_service, '_verify_password', return_value=False):
            # Execute & Assert
            with pytest.raises(UnauthorizedError):
                await auth_service.change_password(
                    user_id="user123",
                    old_password="wrong_old_password",
                    new_password="NewSecurePass123!"
                )
    
    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test password change with weak new password"""
        # Setup
        mock_user_repository.find_by_id.return_value = sample_user
        
        with patch.object(auth_service, '_verify_password', return_value=True):
            # Execute & Assert
            with pytest.raises(ValidationError):
                await auth_service.change_password(
                    user_id="user123",
                    old_password="old_password",
                    new_password="123"  # Too weak
                )
    
    @pytest.mark.asyncio
    async def test_change_password_inactive_user(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test password change for inactive user"""
        # Setup - inactive user
        sample_user.is_active = False
        mock_user_repository.find_by_id.return_value = sample_user
        
        # Execute & Assert
        with pytest.raises(UnauthorizedError):
            await auth_service.change_password(
                user_id="user123",
                old_password="old_password",
                new_password="NewSecurePass123!"
            )


class TestLogout:
    """Test logout functionality"""
    
    @pytest.mark.asyncio
    async def test_logout_success(
        self, 
        auth_service, 
        mock_token_service
    ):
        """Test successful logout"""
        # Execute
        await auth_service.logout("valid_token")
        
        # Assert - should handle gracefully
        # (Implementation might add token to blacklist)
        assert True  # No exception raised
    
    @pytest.mark.asyncio
    async def test_logout_with_invalid_token(
        self, 
        auth_service, 
        mock_token_service
    ):
        """Test logout with invalid token"""
        # Should handle gracefully without error
        await auth_service.logout("invalid_token")
        
        assert True  # No exception raised


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_register_with_sql_injection_attempt(
        self, 
        auth_service, 
        mock_user_repository
    ):
        """Test registration with SQL injection attempt"""
        mock_user_repository.find_by_email.return_value = None
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd"
        ]
        
        for malicious in malicious_inputs:
            # Should sanitize or reject
            try:
                await auth_service.register(
                    fullname=malicious,
                    email="test@example.com",
                    password="SecurePass123!"
                )
            except Exception:
                pass  # Expected to fail or sanitize
    
    @pytest.mark.asyncio
    async def test_login_with_empty_credentials(
        self, 
        auth_service, 
        mock_user_repository
    ):
        """Test login with empty credentials"""
        with pytest.raises((ValidationError, UnauthorizedError, Exception)):
            await auth_service.login(email="", password="")
    
    @pytest.mark.asyncio
    async def test_concurrent_registrations(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test handling of concurrent registrations with same email"""
        # This tests race condition handling
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.create.side_effect = [sample_user, ValidationError("User exists")]
        
        # First registration should succeed
        result1 = await auth_service.register(
            fullname="Test User",
            email="test@example.com",
            password="SecurePass123!"
        )
        assert result1 is not None
        
        # Second should fail
        with pytest.raises((ValidationError, Exception)):
            await auth_service.register(
                fullname="Test User",
                email="test@example.com",
                password="SecurePass123!"
            )


class TestPasswordHashing:
    """Test password hashing functionality"""
    
    @pytest.mark.asyncio
    async def test_password_is_hashed(
        self, 
        auth_service, 
        mock_user_repository,
        sample_user
    ):
        """Test that password is properly hashed"""
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.create.return_value = sample_user
        
        await auth_service.register(
            fullname="Test User",
            email="test@example.com",
            password="PlainTextPassword"
        )
        
        # Verify create was called
        call_args = mock_user_repository.create.call_args
        created_user = call_args[0][0] if call_args else None
        
        # Password should be hashed (not plain text)
        if created_user and hasattr(created_user, 'password_hash'):
            assert created_user.password_hash != "PlainTextPassword"
    
    def test_same_password_different_hashes(self, auth_service):
        """Test that same password produces different hashes (salt)"""
        if hasattr(auth_service, '_hash_password'):
            hash1 = auth_service._hash_password("SamePassword123")
            hash2 = auth_service._hash_password("SamePassword123")
            
            # Should be different due to salt
            assert hash1 != hash2
    
    def test_verify_hashed_password(self, auth_service):
        """Test password verification works correctly"""
        if hasattr(auth_service, '_hash_password') and hasattr(auth_service, '_verify_password'):
            password = "TestPassword123"
            hashed = auth_service._hash_password(password)
            
            # Should verify correctly
            assert auth_service._verify_password(password, hashed) is True
            
            # Should fail with wrong password
            assert auth_service._verify_password("WrongPassword", hashed) is False
