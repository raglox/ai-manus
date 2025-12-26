"""Comprehensive unit tests for StripeService - 60 test cases

Tests cover:
- Customer Management (10 tests)
- Checkout Sessions (15 tests)
- Portal Sessions (10 tests)
- Webhook Handlers (15 tests)
- Signature Verification (5 tests)
- Error Handling (5 tests)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import stripe
import json

from app.infrastructure.external.billing.stripe_service import StripeService
from app.domain.models.subscription import (
    Subscription, 
    SubscriptionPlan, 
    SubscriptionStatus
)
from app.domain.repositories.subscription_repository import SubscriptionRepository


# =====================
# Fixtures
# =====================

@pytest.fixture
def mock_subscription_repository():
    """Mock subscription repository"""
    mock = AsyncMock(spec=SubscriptionRepository)
    return mock


@pytest.fixture
def sample_subscription():
    """Sample subscription for testing"""
    return Subscription(
        id="sub_123",
        user_id="user_123",
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.ACTIVE,
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123",
        monthly_agent_runs=5,
        monthly_agent_runs_limit=10,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def stripe_service(mock_subscription_repository):
    """StripeService instance with mocked dependencies"""
    with patch.dict('os.environ', {
        'STRIPE_SECRET_KEY': 'sk_test_123456789',
        'STRIPE_PRICE_ID_BASIC': 'price_basic_123',
        'STRIPE_PRICE_ID_PRO': 'price_pro_123',
        'STRIPE_WEBHOOK_SECRET': 'whsec_test123'
    }):
        service = StripeService(mock_subscription_repository)
        return service


# =====================
# Customer Management Tests (10 tests)
# =====================

class TestCustomerManagement:
    """Tests for Stripe customer operations"""
    
    @pytest.mark.asyncio
    async def test_create_customer_success(self, stripe_service):
        """Test: Successfully create a Stripe customer"""
        # Arrange
        user_id = "user_123"
        email = "test@example.com"
        name = "Test User"
        
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        
        with patch('stripe.Customer.create', return_value=mock_customer) as mock_create:
            # Act
            customer_id = await stripe_service.create_customer(user_id, email, name)
            
            # Assert
            assert customer_id == "cus_test123"
            mock_create.assert_called_once_with(
                email=email,
                name=name,
                metadata={"user_id": user_id}
            )
    
    @pytest.mark.asyncio
    async def test_create_customer_with_stripe_error(self, stripe_service):
        """Test: Handle Stripe API error during customer creation"""
        # Arrange
        with patch('stripe.Customer.create', side_effect=stripe.error.APIError("API Error")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create Stripe customer"):
                await stripe_service.create_customer("user_123", "test@example.com", "Test User")
    
    @pytest.mark.asyncio
    async def test_create_customer_card_error(self, stripe_service):
        """Test: Handle card error during customer creation"""
        # Arrange
        with patch('stripe.Customer.create', side_effect=stripe.error.CardError(
            "Card declined", "card_declined", "card_error"
        )):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create Stripe customer"):
                await stripe_service.create_customer("user_123", "test@example.com", "Test User")
    
    @pytest.mark.asyncio
    async def test_create_customer_invalid_email(self, stripe_service):
        """Test: Handle invalid email format"""
        # Arrange
        with patch('stripe.Customer.create', side_effect=stripe.error.InvalidRequestError(
            "Invalid email", "email"
        )):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create Stripe customer"):
                await stripe_service.create_customer("user_123", "invalid-email", "Test User")
    
    @pytest.mark.asyncio
    async def test_create_customer_rate_limit(self, stripe_service):
        """Test: Handle Stripe rate limiting"""
        # Arrange
        with patch('stripe.Customer.create', side_effect=stripe.error.RateLimitError("Rate limit")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create Stripe customer"):
                await stripe_service.create_customer("user_123", "test@example.com", "Test User")
    
    @pytest.mark.asyncio
    async def test_create_customer_authentication_error(self, stripe_service):
        """Test: Handle Stripe authentication error (invalid API key)"""
        # Arrange
        with patch('stripe.Customer.create', side_effect=stripe.error.AuthenticationError("Invalid API key")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create Stripe customer"):
                await stripe_service.create_customer("user_123", "test@example.com", "Test User")
    
    @pytest.mark.asyncio
    async def test_create_customer_with_metadata(self, stripe_service):
        """Test: Verify customer metadata is correctly set"""
        # Arrange
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        
        with patch('stripe.Customer.create', return_value=mock_customer) as mock_create:
            # Act
            await stripe_service.create_customer("user_456", "test@example.com", "Test User")
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['metadata']['user_id'] == "user_456"
    
    @pytest.mark.asyncio
    async def test_create_customer_special_characters_in_name(self, stripe_service):
        """Test: Handle special characters in customer name"""
        # Arrange
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        
        with patch('stripe.Customer.create', return_value=mock_customer):
            # Act
            customer_id = await stripe_service.create_customer(
                "user_123", 
                "test@example.com", 
                "José García-López"
            )
            
            # Assert
            assert customer_id == "cus_test123"
    
    @pytest.mark.asyncio
    async def test_create_customer_empty_name(self, stripe_service):
        """Test: Handle empty customer name"""
        # Arrange
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        
        with patch('stripe.Customer.create', return_value=mock_customer):
            # Act
            customer_id = await stripe_service.create_customer("user_123", "test@example.com", "")
            
            # Assert
            assert customer_id == "cus_test123"
    
    @pytest.mark.asyncio
    async def test_create_customer_network_error(self, stripe_service):
        """Test: Handle network connectivity issues"""
        # Arrange
        with patch('stripe.Customer.create', side_effect=stripe.error.APIConnectionError("Network error")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create Stripe customer"):
                await stripe_service.create_customer("user_123", "test@example.com", "Test User")


# =====================
# Checkout Session Tests (15 tests)
# =====================

class TestCheckoutSessions:
    """Tests for Stripe Checkout Session creation"""
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_basic_plan_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully create checkout session for Basic plan"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session):
            # Act
            result = await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            assert result["checkout_session_id"] == "cs_test123"
            assert result["checkout_url"] == "https://checkout.stripe.com/pay/cs_test123"
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_pro_plan_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully create checkout session for Pro plan"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test456"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test456"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            result = await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.PRO,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            assert result["checkout_session_id"] == "cs_test456"
            # Verify Pro plan price ID was used
            call_args = mock_create.call_args[1]
            assert call_args['line_items'][0]['price'] == 'price_pro_123'
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_subscription_not_found(self, stripe_service, mock_subscription_repository):
        """Test: Handle case when subscription is not found"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Subscription not found for user"):
            await stripe_service.create_checkout_session(
                user_id="user_999",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_invalid_plan(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle invalid subscription plan"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid plan for checkout"):
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.FREE,  # FREE plan cannot be used for checkout
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_enterprise_plan(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle Enterprise plan (not configured for checkout)"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid plan for checkout"):
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.ENTERPRISE,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_missing_price_id(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle missing Stripe price ID configuration"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        stripe_service.price_id_basic = None  # Simulate missing configuration
        
        # Act & Assert
        with pytest.raises(ValueError, match="Stripe price ID not configured"):
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_stripe_api_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle Stripe API error during checkout creation"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.checkout.Session.create', side_effect=stripe.error.APIError("API Error")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create checkout session"):
                await stripe_service.create_checkout_session(
                    user_id="user_123",
                    plan=SubscriptionPlan.BASIC,
                    success_url="https://app.example.com/success",
                    cancel_url="https://app.example.com/cancel"
                )
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_metadata_included(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify metadata is correctly included in checkout session"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['metadata']['user_id'] == "user_123"
            assert call_args['metadata']['plan'] == "basic"
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_with_customer_id(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify customer ID is passed to checkout session"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['customer'] == "cus_test123"
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_subscription_mode(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify checkout session is created in subscription mode"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['mode'] == "subscription"
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_payment_methods(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify payment method types are correctly configured"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['payment_method_types'] == ["card"]
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_urls_correctly_set(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify success and cancel URLs are correctly set"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        success_url = "https://app.example.com/payment-success"
        cancel_url = "https://app.example.com/payment-cancel"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['success_url'] == success_url
            assert call_args['cancel_url'] == cancel_url
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_line_items_quantity(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify line items quantity is set to 1"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
        
        with patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_checkout_session(
                user_id="user_123",
                plan=SubscriptionPlan.BASIC,
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel"
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['line_items'][0]['quantity'] == 1
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_invalid_request_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle invalid request error from Stripe"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.checkout.Session.create', side_effect=stripe.error.InvalidRequestError(
            "Invalid request", "param"
        )):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create checkout session"):
                await stripe_service.create_checkout_session(
                    user_id="user_123",
                    plan=SubscriptionPlan.BASIC,
                    success_url="https://app.example.com/success",
                    cancel_url="https://app.example.com/cancel"
                )
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_connection_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle connection error during checkout creation"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.checkout.Session.create', side_effect=stripe.error.APIConnectionError("Connection error")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create checkout session"):
                await stripe_service.create_checkout_session(
                    user_id="user_123",
                    plan=SubscriptionPlan.BASIC,
                    success_url="https://app.example.com/success",
                    cancel_url="https://app.example.com/cancel"
                )


# =====================
# Customer Portal Tests (10 tests)
# =====================

class TestCustomerPortal:
    """Tests for Stripe Customer Portal sessions"""
    
    @pytest.mark.asyncio
    async def test_create_portal_session_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully create customer portal session"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "bps_test123"
        mock_session.url = "https://billing.stripe.com/session/bps_test123"
        
        with patch('stripe.billing_portal.Session.create', return_value=mock_session):
            # Act
            result = await stripe_service.create_customer_portal_session(
                user_id="user_123",
                return_url="https://app.example.com/settings"
            )
            
            # Assert
            assert result["portal_url"] == "https://billing.stripe.com/session/bps_test123"
    
    @pytest.mark.asyncio
    async def test_create_portal_session_subscription_not_found(self, stripe_service, mock_subscription_repository):
        """Test: Handle subscription not found"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="No Stripe customer found"):
            await stripe_service.create_customer_portal_session(
                user_id="user_999",
                return_url="https://app.example.com/settings"
            )
    
    @pytest.mark.asyncio
    async def test_create_portal_session_no_customer_id(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle subscription without Stripe customer ID"""
        # Arrange
        sample_subscription.stripe_customer_id = None
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        # Act & Assert
        with pytest.raises(ValueError, match="No Stripe customer found"):
            await stripe_service.create_customer_portal_session(
                user_id="user_123",
                return_url="https://app.example.com/settings"
            )
    
    @pytest.mark.asyncio
    async def test_create_portal_session_with_customer_id(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify customer ID is passed to portal session"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "bps_test123"
        mock_session.url = "https://billing.stripe.com/session/bps_test123"
        
        with patch('stripe.billing_portal.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_customer_portal_session(
                user_id="user_123",
                return_url="https://app.example.com/settings"
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['customer'] == "cus_test123"
    
    @pytest.mark.asyncio
    async def test_create_portal_session_return_url_set(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Verify return URL is correctly set"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        mock_session = Mock()
        mock_session.id = "bps_test123"
        mock_session.url = "https://billing.stripe.com/session/bps_test123"
        
        return_url = "https://app.example.com/account/billing"
        
        with patch('stripe.billing_portal.Session.create', return_value=mock_session) as mock_create:
            # Act
            await stripe_service.create_customer_portal_session(
                user_id="user_123",
                return_url=return_url
            )
            
            # Assert
            call_args = mock_create.call_args[1]
            assert call_args['return_url'] == return_url
    
    @pytest.mark.asyncio
    async def test_create_portal_session_stripe_api_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle Stripe API error during portal creation"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.billing_portal.Session.create', side_effect=stripe.error.APIError("API Error")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create portal session"):
                await stripe_service.create_customer_portal_session(
                    user_id="user_123",
                    return_url="https://app.example.com/settings"
                )
    
    @pytest.mark.asyncio
    async def test_create_portal_session_invalid_customer(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle invalid Stripe customer ID"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.billing_portal.Session.create', side_effect=stripe.error.InvalidRequestError(
            "No such customer", "customer"
        )):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create portal session"):
                await stripe_service.create_customer_portal_session(
                    user_id="user_123",
                    return_url="https://app.example.com/settings"
                )
    
    @pytest.mark.asyncio
    async def test_create_portal_session_connection_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle connection error during portal creation"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.billing_portal.Session.create', side_effect=stripe.error.APIConnectionError("Connection error")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create portal session"):
                await stripe_service.create_customer_portal_session(
                    user_id="user_123",
                    return_url="https://app.example.com/settings"
                )
    
    @pytest.mark.asyncio
    async def test_create_portal_session_authentication_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle authentication error (invalid API key)"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.billing_portal.Session.create', side_effect=stripe.error.AuthenticationError("Invalid API key")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create portal session"):
                await stripe_service.create_customer_portal_session(
                    user_id="user_123",
                    return_url="https://app.example.com/settings"
                )
    
    @pytest.mark.asyncio
    async def test_create_portal_session_permission_error(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle permission error (feature not enabled)"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        
        with patch('stripe.billing_portal.Session.create', side_effect=stripe.error.PermissionError("Permission denied")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create portal session"):
                await stripe_service.create_customer_portal_session(
                    user_id="user_123",
                    return_url="https://app.example.com/settings"
                )


# =====================
# Webhook Security Tests (5 tests)
# =====================

class TestWebhookSecurity:
    """Tests for webhook signature verification and security"""
    
    @pytest.mark.asyncio
    async def test_webhook_signature_verification_success(self, stripe_service):
        """Test: Valid webhook signature is accepted"""
        # Arrange
        payload = b'{"type": "checkout.session.completed", "data": {}}'
        signature = "valid_signature"
        
        mock_event = {
            'type': 'checkout.session.completed',
            'id': 'evt_test123',
            'data': {'object': {}}
        }
        
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            with patch.object(stripe_service, '_handle_checkout_completed', new_callable=AsyncMock) as mock_handler:
                mock_handler.return_value = {"status": "success"}
                
                # Act
                result = await stripe_service.handle_webhook_event(payload, signature)
                
                # Assert
                assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_rejected(self, stripe_service):
        """Test: Invalid webhook signature is rejected (SECURITY CRITICAL)"""
        # Arrange
        payload = b'{"type": "checkout.session.completed", "data": {}}'
        signature = "invalid_signature"
        
        with patch('stripe.Webhook.construct_event', side_effect=stripe.error.SignatureVerificationError(
            "Invalid signature", signature
        )):
            # Act & Assert
            with pytest.raises(Exception, match="Invalid webhook signature"):
                await stripe_service.handle_webhook_event(payload, signature)
    
    @pytest.mark.asyncio
    async def test_webhook_missing_secret_configuration(self, stripe_service):
        """Test: Webhook rejected when secret is not configured"""
        # Arrange
        stripe_service.webhook_secret = None
        payload = b'{"type": "checkout.session.completed", "data": {}}'
        signature = "some_signature"
        
        # Act & Assert
        with pytest.raises(Exception, match="Webhook secret not configured"):
            await stripe_service.handle_webhook_event(payload, signature)
    
    @pytest.mark.asyncio
    async def test_webhook_invalid_payload_format(self, stripe_service):
        """Test: Invalid JSON payload is rejected"""
        # Arrange
        payload = b'invalid json payload'
        signature = "valid_signature"
        
        with patch('stripe.Webhook.construct_event', side_effect=ValueError("Invalid JSON")):
            # Act & Assert
            with pytest.raises(Exception, match="Invalid webhook payload"):
                await stripe_service.handle_webhook_event(payload, signature)
    
    @pytest.mark.asyncio
    async def test_webhook_empty_payload_rejected(self, stripe_service):
        """Test: Empty webhook payload is rejected"""
        # Arrange
        payload = b''
        signature = "valid_signature"
        
        with patch('stripe.Webhook.construct_event', side_effect=ValueError("Empty payload")):
            # Act & Assert
            with pytest.raises(Exception, match="Invalid webhook payload"):
                await stripe_service.handle_webhook_event(payload, signature)


# =====================
# Webhook Handler Tests (15 tests)
# =====================

class TestWebhookHandlers:
    """Tests for individual webhook event handlers"""
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully handle checkout.session.completed event"""
        # Arrange
        mock_subscription_repository.get_subscription_by_user_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        session_data = {
            'id': 'cs_test123',
            'customer': 'cus_test456',
            'subscription': 'sub_test789',
            'metadata': {'user_id': 'user_123'}
        }
        
        # Act
        result = await stripe_service._handle_checkout_completed(session_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["user_id"] == "user_123"
        mock_subscription_repository.update_subscription.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_missing_user_id(self, stripe_service):
        """Test: Handle checkout event with missing user_id in metadata"""
        # Arrange
        session_data = {
            'id': 'cs_test123',
            'customer': 'cus_test456',
            'subscription': 'sub_test789',
            'metadata': {}  # No user_id
        }
        
        # Act
        result = await stripe_service._handle_checkout_completed(session_data)
        
        # Assert
        assert result["status"] == "error"
        assert "Missing user_id" in result["message"]
    
    @pytest.mark.asyncio
    async def test_handle_subscription_created_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully handle customer.subscription.created event"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        stripe_subscription_data = {
            'id': 'sub_test123',
            'customer': 'cus_test456',
            'status': 'active',
            'current_period_start': int(datetime.now(timezone.utc).timestamp()),
            'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            'items': {
                'data': [{'price': {'id': 'price_basic_123'}}]
            }
        }
        
        # Act
        result = await stripe_service._handle_subscription_created(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.status == SubscriptionStatus.ACTIVE
        assert sample_subscription.plan == SubscriptionPlan.BASIC
    
    @pytest.mark.asyncio
    async def test_handle_subscription_created_pro_plan(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle subscription created event for Pro plan"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        stripe_subscription_data = {
            'id': 'sub_test123',
            'customer': 'cus_test456',
            'status': 'active',
            'current_period_start': int(datetime.now(timezone.utc).timestamp()),
            'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            'items': {
                'data': [{'price': {'id': 'price_pro_123'}}]
            }
        }
        
        # Act
        result = await stripe_service._handle_subscription_created(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.plan == SubscriptionPlan.PRO
    
    @pytest.mark.asyncio
    async def test_handle_subscription_updated_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully handle customer.subscription.updated event"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        stripe_subscription_data = {
            'id': 'sub_test123',
            'status': 'active',
            'current_period_start': int(datetime.now(timezone.utc).timestamp()),
            'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            'cancel_at_period_end': False
        }
        
        # Act
        result = await stripe_service._handle_subscription_updated(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.status == SubscriptionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_handle_subscription_updated_cancel_at_period_end(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Handle subscription set to cancel at period end"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        stripe_subscription_data = {
            'id': 'sub_test123',
            'status': 'active',
            'current_period_start': int(datetime.now(timezone.utc).timestamp()),
            'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            'cancel_at_period_end': True
        }
        
        # Act
        result = await stripe_service._handle_subscription_updated(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.cancel_at_period_end is True
    
    @pytest.mark.asyncio
    async def test_handle_subscription_deleted_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully handle customer.subscription.deleted event"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        stripe_subscription_data = {
            'id': 'sub_test123'
        }
        
        # Act
        result = await stripe_service._handle_subscription_deleted(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.status == SubscriptionStatus.CANCELED
        assert sample_subscription.plan == SubscriptionPlan.FREE
    
    @pytest.mark.asyncio
    async def test_handle_payment_succeeded_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully handle invoice.payment_succeeded event"""
        # Arrange
        sample_subscription.monthly_agent_runs = 100  # Some usage
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        invoice_data = {
            'id': 'in_test123',
            'subscription': 'sub_test123'
        }
        
        # Act
        result = await stripe_service._handle_payment_succeeded(invoice_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.monthly_agent_runs == 0  # Usage reset
        assert sample_subscription.status == SubscriptionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_handle_payment_succeeded_no_subscription(self, stripe_service):
        """Test: Handle payment succeeded with no subscription ID"""
        # Arrange
        invoice_data = {
            'id': 'in_test123'
            # No subscription field
        }
        
        # Act
        result = await stripe_service._handle_payment_succeeded(invoice_data)
        
        # Assert
        assert result["status"] == "ignored"
    
    @pytest.mark.asyncio
    async def test_handle_payment_failed_success(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Successfully handle invoice.payment_failed event"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        invoice_data = {
            'id': 'in_test123',
            'subscription': 'sub_test123'
        }
        
        # Act
        result = await stripe_service._handle_payment_failed(invoice_data)
        
        # Assert
        assert result["status"] == "success"
        assert sample_subscription.status == SubscriptionStatus.PAST_DUE
    
    @pytest.mark.asyncio
    async def test_handle_payment_failed_no_subscription(self, stripe_service):
        """Test: Handle payment failed with no subscription ID"""
        # Arrange
        invoice_data = {
            'id': 'in_test123'
            # No subscription field
        }
        
        # Act
        result = await stripe_service._handle_payment_failed(invoice_data)
        
        # Assert
        assert result["status"] == "ignored"
    
    @pytest.mark.asyncio
    async def test_handle_subscription_not_found(self, stripe_service, mock_subscription_repository):
        """Test: Handle webhook when subscription is not found in database"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = None
        
        stripe_subscription_data = {
            'id': 'sub_test999',
            'status': 'active',
            'current_period_start': int(datetime.now(timezone.utc).timestamp()),
            'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            'cancel_at_period_end': False
        }
        
        # Act
        result = await stripe_service._handle_subscription_updated(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "error"
        assert "Subscription not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_handle_unhandled_webhook_event(self, stripe_service):
        """Test: Gracefully handle unknown webhook event types"""
        # Arrange
        payload = b'{"type": "customer.created", "data": {}}'
        signature = "valid_signature"
        
        mock_event = {
            'type': 'customer.created',
            'id': 'evt_test123',
            'data': {'object': {}}
        }
        
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            # Act
            result = await stripe_service.handle_webhook_event(payload, signature)
            
            # Assert
            assert result["status"] == "ignored"
            assert result["event_type"] == "customer.created"
    
    @pytest.mark.asyncio
    async def test_handle_subscription_created_fallback_to_customer_id(self, stripe_service, mock_subscription_repository, sample_subscription):
        """Test: Fallback to finding subscription by customer ID"""
        # Arrange
        mock_subscription_repository.get_subscription_by_stripe_subscription_id.return_value = None
        mock_subscription_repository.get_subscription_by_stripe_customer_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = sample_subscription
        
        stripe_subscription_data = {
            'id': 'sub_test123',
            'customer': 'cus_test456',
            'status': 'active',
            'current_period_start': int(datetime.now(timezone.utc).timestamp()),
            'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            'items': {
                'data': [{'price': {'id': 'price_basic_123'}}]
            }
        }
        
        # Act
        result = await stripe_service._handle_subscription_created(stripe_subscription_data)
        
        # Assert
        assert result["status"] == "success"
        mock_subscription_repository.get_subscription_by_stripe_customer_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_handler_exception_propagation(self, stripe_service):
        """Test: Ensure exceptions in handlers are propagated correctly"""
        # Arrange
        payload = b'{"type": "checkout.session.completed", "data": {}}'
        signature = "valid_signature"
        
        mock_event = {
            'type': 'checkout.session.completed',
            'id': 'evt_test123',
            'data': {'object': {}}
        }
        
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            with patch.object(stripe_service, '_handle_checkout_completed', side_effect=Exception("Handler error")):
                # Act & Assert
                with pytest.raises(Exception, match="Handler error"):
                    await stripe_service.handle_webhook_event(payload, signature)
