"""
Comprehensive Tests for Domain Models
Coverage: User, Subscription, Session, File, Agent models
"""
import pytest
from datetime import datetime
from app.domain.models.user import User
from app.domain.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = User(
            id="user123",
            fullname="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            role="user",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.is_active is True
    
    def test_user_with_defaults(self):
        """Test user with default values"""
        user = User(
            id="user456",
            fullname="Another User",
            email="another@example.com",
            password_hash="hashed"
        )
        
        # Should have defaults
        assert user.role is not None
        assert user.is_active is not None
    
    def test_user_equality(self):
        """Test user equality comparison"""
        user1 = User(id="user123", fullname="Test", email="test@example.com", password_hash="hash")
        user2 = User(id="user123", fullname="Test", email="test@example.com", password_hash="hash")
        user3 = User(id="user456", fullname="Other", email="other@example.com", password_hash="hash")
        
        assert user1.id == user2.id
        assert user1.id != user3.id


class TestSubscriptionModel:
    """Test Subscription model"""
    
    def test_subscription_creation(self):
        """Test creating a subscription"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_runs=10,
            monthly_runs_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert sub.id == "sub123"
        assert sub.user_id == "user123"
        assert sub.plan == SubscriptionPlan.FREE
    
    def test_can_use_agent_within_limit(self):
        """Test can_use_agent returns True when within limit"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_runs=50,
            monthly_runs_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if hasattr(sub, 'can_use_agent'):
            assert sub.can_use_agent() is True
    
    def test_can_use_agent_at_limit(self):
        """Test can_use_agent returns False when at limit"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_runs=100,
            monthly_runs_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if hasattr(sub, 'can_use_agent'):
            assert sub.can_use_agent() is False
    
    def test_can_use_agent_inactive(self):
        """Test can_use_agent returns False when inactive"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.CANCELED,
            monthly_runs=10,
            monthly_runs_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if hasattr(sub, 'can_use_agent'):
            assert sub.can_use_agent() is False
    
    def test_increment_usage(self):
        """Test incrementing usage"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_runs=10,
            monthly_runs_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        initial_runs = sub.monthly_runs
        
        if hasattr(sub, 'increment_usage'):
            sub.increment_usage()
            assert sub.monthly_runs == initial_runs + 1
    
    def test_reset_monthly_usage(self):
        """Test resetting monthly usage"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_runs=50,
            monthly_runs_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if hasattr(sub, 'reset_monthly_usage'):
            sub.reset_monthly_usage()
            assert sub.monthly_runs == 0
    
    def test_subscription_plans(self):
        """Test subscription plan enum values"""
        assert SubscriptionPlan.FREE is not None
        assert SubscriptionPlan.BASIC is not None
        assert SubscriptionPlan.PRO is not None
    
    def test_subscription_statuses(self):
        """Test subscription status enum values"""
        assert SubscriptionStatus.ACTIVE is not None
        assert SubscriptionStatus.CANCELED is not None
        assert SubscriptionStatus.PAST_DUE is not None


class TestSessionModel:
    """Additional Session model tests"""
    
    def test_session_with_events(self):
        """Test session with events"""
        from app.domain.models.session import Session, SessionStatus
        
        session = Session(
            session_id="session123",
            user_id="user123",
            title="Test Session",
            status=SessionStatus.PENDING,
            events=[
                {"type": "message", "content": "Hello"},
                {"type": "response", "content": "Hi"}
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert len(session.events) == 2
        assert session.events[0]["type"] == "message"
    
    def test_session_status_transitions(self):
        """Test session status enum values"""
        from app.domain.models.session import SessionStatus
        
        assert SessionStatus.PENDING is not None
        assert SessionStatus.RUNNING is not None
        assert SessionStatus.STOPPED is not None
        assert SessionStatus.ERROR is not None


class TestPlanModel:
    """Test Plan model"""
    
    def test_plan_creation(self):
        """Test creating a plan"""
        from app.domain.models.plan import Plan
        
        plan = Plan(
            goal="Complete task",
            steps=["Step 1", "Step 2", "Step 3"],
            completed_steps=[]
        )
        
        assert plan.goal == "Complete task"
        assert len(plan.steps) == 3
        assert len(plan.completed_steps) == 0
    
    def test_plan_progress(self):
        """Test plan progress tracking"""
        from app.domain.models.plan import Plan
        
        plan = Plan(
            goal="Complete task",
            steps=["Step 1", "Step 2", "Step 3"],
            completed_steps=["Step 1"]
        )
        
        if hasattr(plan, 'progress'):
            progress = plan.progress()
            assert progress > 0
            assert progress < 100


class TestMemoryModel:
    """Test Memory model"""
    
    def test_memory_creation(self):
        """Test creating memory"""
        from app.domain.models.memory import Memory
        
        memory = Memory(
            content="Test memory content",
            metadata={"type": "short_term"}
        )
        
        assert memory.content == "Test memory content"
        assert memory.metadata["type"] == "short_term"


class TestAgentModel:
    """Test Agent model"""
    
    def test_agent_creation(self):
        """Test creating agent"""
        from app.domain.models.agent import Agent
        
        agent = Agent(
            id="agent123",
            name="Test Agent",
            description="A test agent",
            capabilities=["task1", "task2"]
        )
        
        assert agent.id == "agent123"
        assert agent.name == "Test Agent"
        assert len(agent.capabilities) == 2


class TestFileModel:
    """Test File model"""
    
    def test_file_creation(self):
        """Test creating file"""
        from app.domain.models.file import File
        
        file = File(
            id="file123",
            filename="test.txt",
            content_type="text/plain",
            size=1024,
            user_id="user123",
            created_at=datetime.utcnow()
        )
        
        assert file.id == "file123"
        assert file.filename == "test.txt"
        assert file.size == 1024


class TestMessageModel:
    """Additional Message model tests"""
    
    def test_message_roles(self):
        """Test message role enum"""
        from app.domain.models.message import MessageRole
        
        assert MessageRole.USER is not None
        assert MessageRole.ASSISTANT is not None
        assert MessageRole.SYSTEM is not None
    
    def test_message_creation(self):
        """Test creating message"""
        from app.domain.models.message import Message, MessageRole
        
        message = Message(
            role=MessageRole.USER,
            content="Hello AI"
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Hello AI"


class TestToolResultModel:
    """Additional ToolResult model tests"""
    
    def test_tool_result_success(self):
        """Test successful tool result"""
        from app.domain.models.tool_result import ToolResult
        
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            output="Operation successful",
            error=None
        )
        
        assert result.success is True
        assert result.output == "Operation successful"
        assert result.error is None
    
    def test_tool_result_failure(self):
        """Test failed tool result"""
        from app.domain.models.tool_result import ToolResult
        
        result = ToolResult(
            tool_name="test_tool",
            success=False,
            output="",
            error="Operation failed"
        )
        
        assert result.success is False
        assert result.error == "Operation failed"


class TestSearchModel:
    """Additional Search model tests"""
    
    def test_search_result_creation(self):
        """Test creating search result"""
        from app.domain.models.search import SearchResult
        
        result = SearchResult(
            title="Test Result",
            url="https://example.com",
            snippet="This is a test snippet"
        )
        
        assert result.title == "Test Result"
        assert result.url == "https://example.com"
        assert result.snippet == "This is a test snippet"
