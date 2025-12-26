"""
Fixed and Updated Domain Models Tests
Tests for actual model structures without expecting non-existent attributes
"""
import pytest
from datetime import datetime, timezone
from app.domain.models.user import User
from app.domain.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.domain.models.session import Session, SessionStatus
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
from app.domain.models.tool_result import ToolResult
from app.domain.models.plan import Plan, Step


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = User(
            id="user123",
            fullname="Test User",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.is_active is True
    
    def test_user_email_validation(self):
        """Test user email must be valid"""
        with pytest.raises(ValueError):
            User(
                id="user123",
                fullname="Test",
                email="invalid-email",
                hashed_password="hash"
            )


class TestSubscriptionModel:
    """Test Subscription model"""
    
    def test_subscription_creation(self):
        """Test creating a subscription"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_agent_runs=5,
            monthly_agent_runs_limit=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert sub.id == "sub123"
        assert sub.user_id == "user123"
        assert sub.plan == SubscriptionPlan.FREE
        assert sub.monthly_agent_runs == 5
        assert sub.monthly_agent_runs_limit == 10
    
    def test_can_use_agent_within_limit(self):
        """Test can_use_agent returns True when within limit"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_agent_runs=5,
            monthly_agent_runs_limit=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert sub.can_use_agent() is True
    
    def test_can_use_agent_at_limit(self):
        """Test can_use_agent returns False when at limit"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_agent_runs=10,
            monthly_agent_runs_limit=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert sub.can_use_agent() is False
    
    def test_increment_usage(self):
        """Test incrementing monthly usage"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_agent_runs=5,
            monthly_agent_runs_limit=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        sub.increment_usage()
        assert sub.monthly_agent_runs == 6
    
    def test_upgrade_to_basic(self):
        """Test upgrading to Basic plan"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_agent_runs=5,
            monthly_agent_runs_limit=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        sub.upgrade_to_basic()
        assert sub.plan == SubscriptionPlan.BASIC
        assert sub.monthly_agent_runs_limit == 1000
        assert sub.monthly_agent_runs == 0  # Reset on upgrade
    
    def test_upgrade_to_pro(self):
        """Test upgrading to Pro plan"""
        sub = Subscription(
            id="sub123",
            user_id="user123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            monthly_agent_runs=5,
            monthly_agent_runs_limit=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        sub.upgrade_to_pro()
        assert sub.plan == SubscriptionPlan.PRO
        assert sub.monthly_agent_runs_limit == 5000
        assert sub.monthly_agent_runs == 0


class TestSessionModel:
    """Test Session model"""
    
    def test_session_creation(self):
        """Test creating a session"""
        session = Session(
            id="sess123",
            user_id="user123",
            agent_id="agent123",
            title="Test Session",
            status=SessionStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert session.id == "sess123"
        assert session.user_id == "user123"
        assert session.agent_id == "agent123"
        assert session.status == SessionStatus.PENDING
    
    def test_session_status_transitions(self):
        """Test session status can transition"""
        session = Session(
            session_id="sess123",
            user_id="user123",
            agent_id="agent123",
            title="Test Session",
            status=SessionStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Transition to running
        session.status = SessionStatus.RUNNING
        assert session.status == SessionStatus.RUNNING
        
        # Transition to completed
        session.status = SessionStatus.COMPLETED
        assert session.status == SessionStatus.COMPLETED


class TestAgentModel:
    """Test Agent model"""
    
    def test_agent_creation(self):
        """Test creating an agent"""
        agent = Agent(
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=2000
        )
        
        assert agent.model_name == "gpt-4"
        assert agent.temperature == 0.7
        assert agent.max_tokens == 2000
        assert agent.id is not None  # Auto-generated
    
    def test_agent_temperature_validation(self):
        """Test temperature validation"""
        with pytest.raises(ValueError, match="Temperature must be between 0 and 1"):
            Agent(
                model_name="gpt-4",
                temperature=1.5,  # Invalid: > 1
                max_tokens=2000
            )
    
    def test_agent_max_tokens_validation(self):
        """Test max tokens validation"""
        with pytest.raises(ValueError, match="Max tokens must be positive"):
            Agent(
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=-100  # Invalid: negative
            )


class TestMemoryModel:
    """Test Memory model"""
    
    def test_memory_creation(self):
        """Test creating memory"""
        memory = Memory()
        
        assert memory.messages == []
        assert memory.empty is True
    
    def test_add_message(self):
        """Test adding a message"""
        memory = Memory()
        message = {"role": "user", "content": "Hello"}
        
        memory.add_message(message)
        assert len(memory.messages) == 1
        assert memory.get_last_message() == message
    
    def test_add_multiple_messages(self):
        """Test adding multiple messages"""
        memory = Memory()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        memory.add_messages(messages)
        assert len(memory.messages) == 2
        assert memory.get_last_message() == messages[1]
    
    def test_roll_back(self):
        """Test rolling back memory"""
        memory = Memory()
        memory.add_message({"role": "user", "content": "Hello"})
        memory.add_message({"role": "assistant", "content": "Hi"})
        
        memory.roll_back()
        assert len(memory.messages) == 1


class TestToolResultModel:
    """Test ToolResult model"""
    
    def test_tool_result_success(self):
        """Test successful tool result"""
        result = ToolResult(
            success=True,
            data={"output": "Result data"}
        )
        
        assert result.success is True
        assert result.data == {"output": "Result data"}
    
    def test_tool_result_failure(self):
        """Test failed tool result"""
        result = ToolResult(
            success=False,
            data=None,
            message="Operation failed"
        )
        
        assert result.success is False
        assert result.message == "Operation failed"


class TestPlanModel:
    """Test Plan model"""
    
    def test_plan_creation(self):
        """Test creating a plan"""
        steps = [
            Step(id="step1", description="Step 1", status="pending"),
            Step(id="step2", description="Step 2", status="pending"),
            Step(id="step3", description="Step 3", status="pending")
        ]
        
        plan = Plan(
            goal="Test goal",
            steps=steps,
            context={}
        )
        
        assert plan.goal == "Test goal"
        assert len(plan.steps) == 3
        assert all(isinstance(s, Step) for s in plan.steps)
    
    def test_plan_progress(self):
        """Test plan progress tracking"""
        steps = [
            Step(id="step1", description="Step 1", status="completed"),
            Step(id="step2", description="Step 2", status="running"),  # Fixed: "running" not "in_progress"
            Step(id="step3", description="Step 3", status="pending")
        ]
        
        plan = Plan(
            goal="Test goal",
            steps=steps,
            context={}
        )
        
        # Check progress
        completed_steps = [s for s in plan.steps if s.status == "completed"]
        assert len(completed_steps) == 1
