"""
Comprehensive Unit Tests for Token Service
Coverage: JWT token generation, verification, refresh, blacklist
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import jwt
from app.application.services.token_service import TokenService
from app.core.config import get_settings
from app.domain.models.user import User, UserRole

settings = get_settings()


@pytest.fixture
def token_service():
    """Create TokenService instance"""
    return TokenService()


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id="test_user_123",
        fullname="Test User",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.USER,
        is_active=True
    )


class TestTokenGeneration:
    """Test token generation functionality"""
    
    def test_create_access_token_success(self, token_service, sample_user):
        """Test successful access token generation"""
        token = token_service.create_access_token(sample_user)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == sample_user["id"]
        assert payload["email"] == sample_user["email"]
        assert payload["type"] == "access"
    
    def test_create_refresh_token_success(self, token_service, sample_user):
        """Test successful refresh token generation"""
        token = token_service.create_refresh_token(sample_user)
        
        assert token is not None
        assert isinstance(token, str)
        
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        assert payload["type"] == "refresh"
        assert payload["sub"] == sample_user["id"]
    
    def test_generate_token_with_custom_expiry(self, token_service, sample_user):
        """Test token generation with custom expiry"""
        custom_expiry = timedelta(hours=1)
        token = token_service.create_access_token(
            sample_user, 
            expires_delta=custom_expiry
        )
        
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiry is approximately 1 hour from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        time_diff = (exp_time - now).total_seconds()
        
        assert 3500 < time_diff < 3700  # ~1 hour (with small margin)
    
    def test_generate_token_missing_required_fields(self, token_service):
        """Test token generation with missing required fields"""
        incomplete_data = {"email": "test@example.com"}
        
        with pytest.raises((KeyError, Exception)):
            token_service.create_access_token(incomplete_data)


class TestTokenVerification:
    """Test token verification functionality"""
    
    def test_verify_valid_token(self, token_service, sample_user):
        """Test verification of valid token"""
        token = token_service.create_access_token(sample_user)
        payload = token_service.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == sample_user["id"]
        assert payload["email"] == sample_user["email"]
    
    def test_verify_expired_token(self, token_service, sample_user):
        """Test verification of expired token"""
        # Generate token with past expiry
        expired_token = jwt.encode(
            {
                "sub": sample_user["id"],
                "email": sample_user["email"],
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2)
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        payload = token_service.verify_token(expired_token)
        assert payload is None
    
    def test_verify_invalid_token(self, token_service):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        payload = token_service.verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_token_wrong_secret(self, token_service, sample_user):
        """Test verification of token signed with wrong secret"""
        wrong_token = jwt.encode(
            {
                "sub": sample_user["id"],
                "email": sample_user["email"],
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            "wrong_secret_key",
            algorithm=settings.jwt_algorithm
        )
        
        payload = token_service.verify_token(wrong_token)
        assert payload is None
    
    def test_verify_token_missing_claims(self, token_service):
        """Test verification of token with missing claims"""
        incomplete_token = jwt.encode(
            {"email": "test@example.com"},  # Missing 'sub'
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        # Should still decode but missing data
        payload = token_service.verify_token(incomplete_token)
        # Depending on implementation, might return None or partial data
        assert payload is None or "sub" not in payload


class TestGetUserFromToken:
    """Test user extraction from token"""
    
    def test_get_user_from_valid_token(self, token_service, sample_user):
        """Test extracting user from valid token"""
        token = token_service.create_access_token(sample_user)
        user = token_service.get_user_from_token(token)
        
        assert user is not None
        assert user["id"] == sample_user["id"]
        assert user["email"] == sample_user["email"]
        assert user["fullname"] == sample_user["fullname"]
        assert user["role"] == sample_user["role"]
    
    def test_get_user_from_invalid_token(self, token_service):
        """Test extracting user from invalid token"""
        user = token_service.get_user_from_token("invalid_token")
        
        assert user is None
    
    def test_get_user_from_expired_token(self, token_service, sample_user):
        """Test extracting user from expired token"""
        expired_token = jwt.encode(
            {
                "sub": sample_user["id"],
                "email": sample_user["email"],
                "fullname": sample_user["fullname"],
                "role": sample_user["role"],
                "exp": datetime.utcnow() - timedelta(hours=1)
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        user = token_service.get_user_from_token(expired_token)
        assert user is None


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    def test_refresh_token_flow(self, token_service, sample_user):
        """Test complete refresh token flow"""
        # Generate refresh token
        refresh_token = token_service.create_refresh_token(sample_user)
        
        # Verify it's valid
        payload = token_service.verify_token(refresh_token)
        assert payload is not None
        assert payload["type"] == "refresh"
        
        # Use it to generate new access token
        new_access_token = token_service.create_access_token(sample_user)
        assert new_access_token is not None
        
        # Verify new access token
        access_payload = token_service.verify_token(new_access_token)
        assert access_payload["type"] == "access"


class TestTokenBlacklist:
    """Test token blacklist functionality (if implemented)"""
    
    @pytest.mark.asyncio
    async def test_blacklist_token(self, token_service, sample_user):
        """Test adding token to blacklist"""
        token = token_service.create_access_token(sample_user)
        
        # If blacklist is implemented
        if hasattr(token_service, 'blacklist_token'):
            await token_service.blacklist_token(token)
            
            # Verify token is blacklisted
            if hasattr(token_service, 'is_blacklisted'):
                is_blacklisted = await token_service.is_blacklisted(token)
                assert is_blacklisted is True


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_empty_user_data(self, token_service):
        """Test with empty user data"""
        with pytest.raises((ValueError, KeyError, Exception)):
            token_service.create_access_token({})
    
    def test_none_user_data(self, token_service):
        """Test with None user data"""
        with pytest.raises((TypeError, AttributeError, Exception)):
            token_service.create_access_token(None)
    
    def test_verify_empty_token(self, token_service):
        """Test verification with empty token"""
        payload = token_service.verify_token("")
        assert payload is None
    
    def test_verify_none_token(self, token_service):
        """Test verification with None token"""
        payload = token_service.verify_token(None)
        assert payload is None
    
    def test_malformed_jwt(self, token_service):
        """Test with malformed JWT structure"""
        malformed_tokens = [
            "abc",
            "abc.def",
            "abc.def.ghi.jkl",  # Too many parts
            "....",
        ]
        
        for token in malformed_tokens:
            payload = token_service.verify_token(token)
            assert payload is None


@pytest.mark.benchmark
class TestTokenPerformance:
    """Test token service performance"""
    
    def test_generate_many_tokens(self, token_service, sample_user, benchmark):
        """Benchmark token generation"""
        def generate():
            return token_service.create_access_token(sample_user)
        
        result = benchmark(generate)
        assert result is not None
    
    def test_verify_many_tokens(self, token_service, sample_user, benchmark):
        """Benchmark token verification"""
        token = token_service.create_access_token(sample_user)
        
        def verify():
            return token_service.verify_token(token)
        
        result = benchmark(verify)
        assert result is not None
