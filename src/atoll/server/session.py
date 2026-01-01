"""Session management for stateful conversations in REST API."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ConversationSession:
    """Represents a conversation session."""

    session_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append({"role": role, "content": content})
        self.last_accessed = datetime.now()

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        return datetime.now() - self.last_accessed > timedelta(minutes=timeout_minutes)


class SessionManager:
    """Manages conversation sessions for REST API."""

    def __init__(self, session_timeout_minutes: int = 30):
        """Initialize session manager.

        Args:
            session_timeout_minutes: Session expiration timeout in minutes
        """
        self.sessions: dict[str, ConversationSession] = {}
        self.timeout_minutes = session_timeout_minutes

    def create_session(self) -> str:
        """Create a new conversation session.

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationSession(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a conversation session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session and session.is_expired(self.timeout_minutes):
            # Clean up expired session
            del self.sessions[session_id]
            return None
        return session

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to a session.

        Args:
            session_id: Session identifier
            role: Message role (user/assistant/system)
            content: Message content

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session:
            session.add_message(role, content)
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired = [
            sid
            for sid, session in self.sessions.items()
            if session.is_expired(self.timeout_minutes)
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)

    def get_session_count(self) -> int:
        """Get the number of active sessions.

        Returns:
            Count of active sessions
        """
        return len(self.sessions)
