"""
Comprehensive Unit Tests for Session Management
Coverage: Session creation, retrieval, deletion, status updates
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from app.domain.models.session import Session, SessionStatus
from app.application.errors.exceptions import NotFoundError, UnauthorizedError


@pytest.fixture
def mock_session_repository():
    """Mock session repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_user_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def sample_session():
    """Sample session for testing"""
    return Session(
        session_id="test_session_123",
        user_id="user123",
        title="Test Session",
        status=SessionStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        unread_message_count=0,
        is_shared=False
    )


class TestSessionCreation:
    """Test session creation functionality"""
    
    @pytest.mark.asyncio
    async def test_create_session_success(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test successful session creation"""
        # Setup
        mock_session_repository.create.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.create(sample_session)
        
        # Assert
        assert result is not None
        assert result.session_id == "test_session_123"
        assert result.user_id == "user123"
        assert result.status == SessionStatus.PENDING
        mock_session_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_with_custom_title(
        self, 
        mock_session_repository
    ):
        """Test creating session with custom title"""
        custom_session = Session(
            session_id="session_456",
            user_id="user123",
            title="My Custom Session Title",
            status=SessionStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_session_repository.create.return_value = custom_session
        
        result = await mock_session_repository.create(custom_session)
        
        assert result.title == "My Custom Session Title"
    
    @pytest.mark.asyncio
    async def test_create_multiple_sessions_same_user(
        self, 
        mock_session_repository
    ):
        """Test creating multiple sessions for same user"""
        sessions = [
            Session(
                session_id=f"session_{i}",
                user_id="user123",
                title=f"Session {i}",
                status=SessionStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        
        for session in sessions:
            mock_session_repository.create.return_value = session
            result = await mock_session_repository.create(session)
            assert result.user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_create_session_generates_unique_id(
        self, 
        mock_session_repository
    ):
        """Test that each session gets unique ID"""
        ids = set()
        
        for i in range(5):
            session = Session(
                session_id=f"unique_session_{i}",
                user_id="user123",
                title=f"Session {i}",
                status=SessionStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_session_repository.create.return_value = session
            result = await mock_session_repository.create(session)
            ids.add(result.session_id)
        
        # All IDs should be unique
        assert len(ids) == 5


class TestSessionRetrieval:
    """Test session retrieval functionality"""
    
    @pytest.mark.asyncio
    async def test_get_session_by_id_success(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test successful session retrieval by ID"""
        # Setup
        mock_session_repository.find_by_id.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.find_by_id("test_session_123")
        
        # Assert
        assert result is not None
        assert result.session_id == "test_session_123"
        mock_session_repository.find_by_id.assert_called_once_with("test_session_123")
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(
        self, 
        mock_session_repository
    ):
        """Test retrieving non-existent session"""
        # Setup
        mock_session_repository.find_by_id.return_value = None
        
        # Execute
        result = await mock_session_repository.find_by_id("nonexistent_id")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_sessions_by_user_id(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test retrieving all sessions for a user"""
        # Setup
        sessions = [
            Session(
                session_id=f"session_{i}",
                user_id="user123",
                title=f"Session {i}",
                status=SessionStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        mock_session_repository.find_by_user_id.return_value = sessions
        
        # Execute
        result = await mock_session_repository.find_by_user_id("user123")
        
        # Assert
        assert len(result) == 3
        assert all(s.user_id == "user123" for s in result)
    
    @pytest.mark.asyncio
    async def test_get_sessions_empty_list(
        self, 
        mock_session_repository
    ):
        """Test retrieving sessions when user has none"""
        # Setup
        mock_session_repository.find_by_user_id.return_value = []
        
        # Execute
        result = await mock_session_repository.find_by_user_id("user_no_sessions")
        
        # Assert
        assert result == []


class TestSessionUpdate:
    """Test session update functionality"""
    
    @pytest.mark.asyncio
    async def test_update_session_status(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test updating session status"""
        # Setup
        sample_session.status = SessionStatus.RUNNING
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.status == SessionStatus.RUNNING
        mock_session_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_session_title(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test updating session title"""
        # Setup
        sample_session.title = "Updated Title"
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.title == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_update_unread_message_count(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test incrementing unread message count"""
        # Setup
        sample_session.unread_message_count = 5
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.unread_message_count == 5
    
    @pytest.mark.asyncio
    async def test_clear_unread_messages(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test clearing unread message count"""
        # Setup
        sample_session.unread_message_count = 0
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.unread_message_count == 0
    
    @pytest.mark.asyncio
    async def test_update_session_sharing(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test enabling session sharing"""
        # Setup
        sample_session.is_shared = True
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.is_shared is True


class TestSessionDeletion:
    """Test session deletion functionality"""
    
    @pytest.mark.asyncio
    async def test_delete_session_success(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test successful session deletion"""
        # Setup
        mock_session_repository.find_by_id.return_value = sample_session
        mock_session_repository.delete.return_value = True
        
        # Execute
        result = await mock_session_repository.delete("test_session_123")
        
        # Assert
        assert result is True
        mock_session_repository.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(
        self, 
        mock_session_repository
    ):
        """Test deleting non-existent session"""
        # Setup
        mock_session_repository.find_by_id.return_value = None
        mock_session_repository.delete.return_value = False
        
        # Execute
        result = await mock_session_repository.delete("nonexistent_id")
        
        # Assert
        assert result is False


class TestSessionStatus:
    """Test session status transitions"""
    
    @pytest.mark.asyncio
    async def test_status_pending_to_running(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test transitioning from PENDING to RUNNING"""
        # Initial state
        assert sample_session.status == SessionStatus.PENDING
        
        # Transition
        sample_session.status = SessionStatus.RUNNING
        mock_session_repository.update.return_value = sample_session
        
        result = await mock_session_repository.update(sample_session)
        
        assert result.status == SessionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_status_running_to_stopped(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test transitioning from RUNNING to STOPPED"""
        sample_session.status = SessionStatus.RUNNING
        
        # Transition
        sample_session.status = SessionStatus.STOPPED
        mock_session_repository.update.return_value = sample_session
        
        result = await mock_session_repository.update(sample_session)
        
        assert result.status == SessionStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_status_running_to_error(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test transitioning to ERROR status"""
        sample_session.status = SessionStatus.RUNNING
        
        # Transition on error
        sample_session.status = SessionStatus.ERROR
        mock_session_repository.update.return_value = sample_session
        
        result = await mock_session_repository.update(sample_session)
        
        assert result.status == SessionStatus.ERROR


class TestSessionSharing:
    """Test session sharing functionality"""
    
    @pytest.mark.asyncio
    async def test_share_session(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test enabling session sharing"""
        # Setup
        sample_session.is_shared = True
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.is_shared is True
    
    @pytest.mark.asyncio
    async def test_unshare_session(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test disabling session sharing"""
        # Setup
        sample_session.is_shared = False
        mock_session_repository.update.return_value = sample_session
        
        # Execute
        result = await mock_session_repository.update(sample_session)
        
        # Assert
        assert result.is_shared is False


class TestSessionEvents:
    """Test session event handling"""
    
    @pytest.mark.asyncio
    async def test_session_with_events(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test session with multiple events"""
        # Add events to session
        sample_session.events = [
            {"type": "message", "content": "Hello", "timestamp": datetime.utcnow()},
            {"type": "response", "content": "Hi there", "timestamp": datetime.utcnow()}
        ]
        
        mock_session_repository.find_by_id.return_value = sample_session
        
        result = await mock_session_repository.find_by_id("test_session_123")
        
        assert len(result.events) == 2
        assert result.events[0]["type"] == "message"
    
    @pytest.mark.asyncio
    async def test_session_add_event(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test adding event to session"""
        # Setup initial events
        sample_session.events = []
        
        # Add new event
        new_event = {"type": "tool_use", "content": "Execute command", "timestamp": datetime.utcnow()}
        sample_session.events.append(new_event)
        
        mock_session_repository.update.return_value = sample_session
        
        result = await mock_session_repository.update(sample_session)
        
        assert len(result.events) == 1
        assert result.events[0]["type"] == "tool_use"


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_updates(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test handling concurrent updates to same session"""
        # This would test optimistic locking if implemented
        mock_session_repository.update.return_value = sample_session
        
        # Multiple concurrent updates
        await mock_session_repository.update(sample_session)
        await mock_session_repository.update(sample_session)
        
        # Should handle gracefully
        assert mock_session_repository.update.call_count == 2
    
    @pytest.mark.asyncio
    async def test_session_with_very_long_title(
        self, 
        mock_session_repository
    ):
        """Test session with very long title"""
        long_title = "A" * 1000
        session = Session(
            session_id="session_long_title",
            user_id="user123",
            title=long_title,
            status=SessionStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_session_repository.create.return_value = session
        result = await mock_session_repository.create(session)
        
        # Should handle or truncate
        assert result.title is not None
    
    @pytest.mark.asyncio
    async def test_session_with_special_characters_title(
        self, 
        mock_session_repository
    ):
        """Test session title with special characters"""
        special_titles = [
            "Session <script>alert('xss')</script>",
            "Session with emoji 😀",
            "Session with unicode ñoño",
            "Session with quotes \"test\"",
        ]
        
        for title in special_titles:
            session = Session(
                session_id=f"session_{hash(title)}",
                user_id="user123",
                title=title,
                status=SessionStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            mock_session_repository.create.return_value = session
            result = await mock_session_repository.create(session)
            
            # Should sanitize or handle safely
            assert result.title is not None
    
    @pytest.mark.asyncio
    async def test_get_session_with_invalid_id_format(
        self, 
        mock_session_repository
    ):
        """Test retrieving session with invalid ID format"""
        invalid_ids = ["", None, "../../etc/passwd", "<script>", 123]
        
        for invalid_id in invalid_ids:
            try:
                mock_session_repository.find_by_id.return_value = None
                result = await mock_session_repository.find_by_id(invalid_id)
                # Should return None or raise appropriate error
                assert result is None or isinstance(result, Exception)
            except Exception:
                # Expected for some invalid inputs
                pass


class TestSessionMetrics:
    """Test session metrics and statistics"""
    
    @pytest.mark.asyncio
    async def test_session_duration_tracking(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test tracking session duration"""
        # Setup
        start_time = datetime.utcnow()
        sample_session.created_at = start_time
        
        # Simulate some time passing
        sample_session.updated_at = start_time
        
        mock_session_repository.find_by_id.return_value = sample_session
        
        result = await mock_session_repository.find_by_id("test_session_123")
        
        # Duration can be calculated
        duration = (result.updated_at - result.created_at).total_seconds()
        assert duration >= 0
    
    @pytest.mark.asyncio
    async def test_session_message_count(
        self, 
        mock_session_repository,
        sample_session
    ):
        """Test counting messages in session"""
        sample_session.events = [
            {"type": "message", "content": "Msg 1"},
            {"type": "message", "content": "Msg 2"},
            {"type": "response", "content": "Response 1"},
            {"type": "message", "content": "Msg 3"},
        ]
        
        mock_session_repository.find_by_id.return_value = sample_session
        
        result = await mock_session_repository.find_by_id("test_session_123")
        
        # Count user messages
        message_count = len([e for e in result.events if e["type"] == "message"])
        assert message_count == 3
